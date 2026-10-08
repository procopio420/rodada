package com.rodada.attendance.operations

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.rodada.attendance.auth.AuthApiException
import com.rodada.attendance.auth.StoredSession
import kotlinx.coroutines.launch
import java.io.IOException
import java.util.UUID

data class OperationsUiState(
    val loading: Boolean = false,
    val submitting: Boolean = false,
    val tabs: List<TabSummary> = emptyList(),
    val products: List<Product> = emptyList(),
    val deliveryTasks: List<DeliveryTask> = emptyList(),
    val selectedTab: TabDetail? = null,
    val cart: List<CartLine> = emptyList(),
    val errorMessage: String? = null,
    val noticeMessage: String? = null,
    /** Kept for the complete UI/ViewModel lifecycle and reused by a retry of this cart. */
    val orderIntentId: String? = null,
    val paymentIntentId: String? = null,
)

class OperationsViewModel(private val repository: OperationsRepository) : ViewModel() {
    var state by mutableStateOf(OperationsUiState())
        private set

    private var loadedSessionKey: String? = null

    fun ensureLoaded(session: StoredSession) {
        val key = session.staffId + ":" + session.venueId
        if (loadedSessionKey == key && (state.tabs.isNotEmpty() || state.loading)) return
        if (loadedSessionKey != null && loadedSessionKey != key) {
            // Never leave a prior operator's draft cart or Tab context on a shared device.
            state = OperationsUiState()
        }
        loadedSessionKey = key
        refresh(session)
    }

    fun refresh(session: StoredSession) {
        state = state.copy(loading = true, errorMessage = null, noticeMessage = null)
        viewModelScope.launch {
            runCatching {
                val tabs = repository.tabs(session)
                val products = repository.products(session)
                val deliveries = repository.deliveryTasks(session)
                val detail = state.selectedTab?.summary?.id?.let { id ->
                    runCatching { repository.tabDetail(session, id) }.getOrNull()
                }
                RefreshSnapshot(tabs, products, deliveries, detail)
            }.onSuccess { snapshot ->
                state = state.copy(
                    loading = false,
                    tabs = snapshot.tabs,
                    products = snapshot.products,
                    deliveryTasks = snapshot.deliveryTasks,
                    selectedTab = snapshot.detail ?: state.selectedTab,
                )
            }.onFailure {
                state = state.copy(loading = false)
                showFailure(it)
            }
        }
    }

    fun openTab(session: StoredSession, label: String) = action {
        val opened = repository.openTab(session, label)
        val detail = repository.tabDetail(session, opened.id)
        state = state.copy(
            tabs = listOf(opened) + state.tabs.filterNot { it.id == opened.id },
            selectedTab = detail,
            cart = emptyList(),
            noticeMessage = "Comanda aberta.",
        )
    }

    fun selectTab(session: StoredSession, tabId: String) = action {
        val detail = repository.tabDetail(session, tabId)
        state = state.copy(selectedTab = detail, cart = emptyList(), orderIntentId = null)
    }

    fun clearSelection() {
        state = state.copy(selectedTab = null, cart = emptyList(), orderIntentId = null)
    }

    fun addProduct(product: Product) {
        if (
            !product.active ||
                product.availability != "AVAILABLE" ||
                state.selectedTab?.summary?.state == "CLOSED" ||
                state.orderIntentId != null
        ) return
        val existing = state.cart.firstOrNull { it.product.id == product.id }
        val next =
            if (existing == null) state.cart + CartLine(product, 1)
            else state.cart.map { if (it.product.id == product.id) it.copy(quantity = it.quantity + 1) else it }
        state = state.copy(cart = next, noticeMessage = null)
    }

    fun changeCartQuantity(productId: String, delta: Int) {
        if (state.orderIntentId != null) return
        val next = state.cart.mapNotNull { line ->
            if (line.product.id != productId) line
            else line.copy(quantity = line.quantity + delta).takeIf { it.quantity > 0 }
        }
        state = state.copy(cart = next)
    }

    fun confirmOrder(session: StoredSession) {
        val tab = state.selectedTab?.summary ?: return
        if (state.cart.isEmpty() || tab.state == "CLOSED" || state.submitting) return
        val intentId = state.orderIntentId ?: UUID.randomUUID().toString()
        state = state.copy(submitting = true, errorMessage = null, noticeMessage = null, orderIntentId = intentId)
        viewModelScope.launch {
            runCatching {
                repository.confirmOrder(session, tab.id, state.cart, intentId)
                repository.tabDetail(session, tab.id)
            }.onSuccess { detail ->
                replaceDetail(detail)
                state = state.copy(
                    submitting = false,
                    cart = emptyList(),
                    noticeMessage = "Pedido enviado para produção.",
                    orderIntentId = null,
                )
            }.onFailure { error ->
                // Retrying this exact cart retains the same intent UUID. The API returns the
                // original Order instead of creating a second order after an ambiguous timeout.
                state = state.copy(submitting = false, orderIntentId = intentId)
                showFailure(error, "Você pode confirmar novamente: o mesmo pedido será reconciliado com segurança.")
            }
        }
    }

    fun collectPayment(session: StoredSession, amountCents: Long, method: PaymentMethod) {
        val tab = state.selectedTab?.summary ?: return
        if (amountCents <= 0 || amountCents > tab.exposureCents || state.submitting) return
        val key = state.paymentIntentId ?: UUID.randomUUID().toString()
        state = state.copy(submitting = true, errorMessage = null, noticeMessage = null, paymentIntentId = key)
        viewModelScope.launch {
            runCatching {
                repository.collectPayment(session, tab.id, amountCents, method, key)
                repository.tabDetail(session, tab.id)
            }.onSuccess { detail ->
                replaceDetail(detail)
                state = state.copy(submitting = false, paymentIntentId = null, noticeMessage = "Pagamento registrado.")
            }.onFailure { error ->
                // Retrying this same action uses the same idempotency key and is safe server-side.
                state = state.copy(submitting = false)
                showFailure(error, "Você pode tentar novamente: a mesma cobrança será reconciliada com segurança.")
            }
        }
    }

    fun closeTab(session: StoredSession) {
        val tab = state.selectedTab?.summary ?: return
        if (state.submitting) return
        state = state.copy(submitting = true, errorMessage = null, noticeMessage = null)
        viewModelScope.launch {
            runCatching {
                repository.closeTab(session, tab.id)
                repository.tabDetail(session, tab.id)
            }.onSuccess { detail ->
                replaceDetail(detail)
                state = state.copy(submitting = false, noticeMessage = "Comanda fechada.")
            }.onFailure { error ->
                state = state.copy(submitting = false)
                showFailure(error)
            }
        }
    }

    fun completeDelivery(session: StoredSession, taskId: String) = action {
        repository.completeDelivery(session, taskId)
        state = state.copy(
            deliveryTasks = repository.deliveryTasks(session),
            noticeMessage = "Entrega concluída.",
        )
    }

    fun dismissMessage() {
        state = state.copy(errorMessage = null, noticeMessage = null)
    }

    private fun replaceDetail(detail: TabDetail) {
        state = state.copy(
            selectedTab = detail,
            tabs = listOf(detail.summary) + state.tabs.filterNot { it.id == detail.summary.id },
        )
    }

    private fun action(block: suspend () -> Unit) {
        if (state.submitting) return
        state = state.copy(submitting = true, errorMessage = null, noticeMessage = null)
        viewModelScope.launch {
            runCatching { block() }
                .onSuccess { state = state.copy(submitting = false) }
                .onFailure {
                    state = state.copy(submitting = false)
                    showFailure(it)
                }
        }
    }

    private fun showFailure(error: Throwable, suffix: String = "") {
        val message =
            when (error) {
                is OperationsApiException -> "${error.code}: ${error.message}"
                is AuthApiException -> "${error.code}: ${error.message}"
                is IOException -> "Sem conexão com o Rodada."
                else -> error.message ?: "Falha inesperada."
            }
        state = state.copy(errorMessage = listOf(message, suffix).filter(String::isNotBlank).joinToString(" "))
    }

    companion object {
        fun factory(repository: OperationsRepository): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T = OperationsViewModel(repository) as T
            }
    }

    private data class RefreshSnapshot(
        val tabs: List<TabSummary>,
        val products: List<Product>,
        val deliveryTasks: List<DeliveryTask>,
        val detail: TabDetail?,
    )
}
