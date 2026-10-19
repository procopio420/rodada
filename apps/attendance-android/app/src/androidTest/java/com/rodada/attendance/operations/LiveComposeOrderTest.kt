package com.rodada.attendance.operations

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import com.rodada.attendance.MainActivity
import com.rodada.attendance.BuildConfig
import com.rodada.attendance.auth.SecureSessionStore
import com.rodada.attendance.auth.AuthHttpClient
import com.rodada.attendance.auth.AuthApiException
import com.rodada.attendance.auth.StoredSession
import com.rodada.attendance.auth.LoginRequest
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test

/** Opt-in UI proof. MainActivity uses production repositories and the disposable Django stack. */
class LiveComposeOrderTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()

    private fun waitText(text: String) {
        compose.waitUntil(30_000) { compose.onAllNodesWithText(text).fetchSemanticsNodes().isNotEmpty() }
    }

    @Test fun confirmThroughProductionCompose() {
        assumeTrue("Disposable runner only", InstrumentationRegistry.getArguments().getString("liveCompose") == "true")
        check(BuildConfig.RODADA_API_BASE_URL == "http://10.0.2.2:8101/")
        waitText("Estabelecimento")
        compose.onNodeWithText("Estabelecimento").performTextInput("android-post-drop-ci")
        compose.onNodeWithText("Operador").performTextInput("android-post-drop-operator")
        compose.onNodeWithText("PIN").performTextInput("2468")
        compose.onNodeWithText("Entrar").performClick()
        compose.waitUntil(30_000) { compose.onAllNodes(hasTestTag("attendance-order") and isEnabled()).fetchSemanticsNodes().isNotEmpty() }
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val session = SecureSessionStore(context).load() ?: error("Missing real UI session")
        val operations = OperationsHttpClient(BuildConfig.RODADA_API_BASE_URL)
        val existingTabIds = operations.tabs(session.tokens.accessToken).map { it.id }.toSet()
        compose.onNodeWithTag("attendance-order").assertIsEnabled().performClick()
        val newTab = hasText("Nova comanda sem mesa") and hasAnyAncestor(isDialog())
        compose.waitUntil(30_000) { compose.onAllNodes(newTab and isEnabled()).fetchSemanticsNodes().isNotEmpty() }
        compose.onNode(newTab).assertIsEnabled().performClick()
        waitText("Nome ou apelido")
        compose.onNodeWithText("Nome ou apelido").performTextInput(InstrumentationRegistry.getArguments().getString("tabLabel") ?: error("Missing isolated run label"))
        compose.onNodeWithText("Abrir", useUnmergedTree = false).performClick()
        compose.waitUntil(30_000) { compose.onAllNodesWithTag("workspace-list").fetchSemanticsNodes().isNotEmpty() }
        // Only Compose creates the Tab; identify its canonical readback by the new ID,
        // independent of labels and ordering in this disposable runner.
        val originalTabId = operations.tabs(session.tokens.accessToken)
            .single { it.id !in existingTabIds }.id
        check(operations.tabDetail(session.tokens.accessToken, originalTabId).summary.exposureCents == 0L)
        for (product in listOf("Android Compose Test Meal", "Android Post Drop Test Soda")) {
            // PR #195: select category, product, quantity; the old flat "Adicionar" action no longer exists.
            compose.onNodeWithTag("workspace-list").performScrollToNode(hasText("Buscar no catálogo"))
            compose.onNodeWithText("Buscar no catálogo").performTextReplacement(product)
            compose.onNodeWithTag("catalog-category-Outros").assertIsEnabled().performClick()
            compose.onNode(hasText(product) and hasClickAction() and hasAnyAncestor(hasTestTag("category-products"))).assertIsEnabled().performClick()
            compose.onNode(hasText("Adicionar ·", substring = true) and hasClickAction()).assertIsEnabled().performScrollTo().performClick()
            compose.onNodeWithText("Voltar às categorias").performClick()
        }
        waitText("Ver pedido atual · 2 itens · R$ 17,00")
        compose.onNodeWithTag("workspace-Pedido atual").performClick()
        waitText("Confirmar pedido")
        val fault = InstrumentationRegistry.getArguments().getString("catalogFault") == "true"
        val revokedFault = InstrumentationRegistry.getArguments().getString("revocationFault") == "true"
        val offlineFault = InstrumentationRegistry.getArguments().getString("offlineFault") == "true"
        var originalPending: RecoveryIntent.ConfirmOrder? = null
        if (fault) {
            // Host controls only the real backend fault; all order actions remain Compose taps.
            val files = InstrumentationRegistry.getInstrumentation().targetContext.filesDir
            java.io.File(files, "catalog-cart-ready").writeText("ready")
            compose.waitUntil(60_000) { java.io.File(files, "catalog-fault-applied").exists() }
        }
        if (offlineFault) waitText("SEM SINAL")
        val confirmation = compose.onNodeWithText("Confirmar pedido").assertIsEnabled().performScrollTo()
        if (fault) confirmation.performClick() else confirmation.performTouchInput { doubleClick() }
        if (offlineFault) {
            val context = InstrumentationRegistry.getInstrumentation().targetContext
            val session = SecureSessionStore(context).load() ?: error("Missing real UI session")
            val queue = PendingMutationIntentStore(context)
            compose.waitUntil(30_000) { queue.orderQueue(session).size == 1 }
            originalPending = queue.orderQueue(session).single()
            check(originalPending!!.state == RecoveryState.PENDING)
            java.io.File(context.filesDir, "offline-session-id").writeText(session.sessionId)
            java.io.File(context.filesDir, "offline-intent-ready").writeText("pending")
            if (revokedFault) {
                compose.waitUntil(60_000) { java.io.File(context.filesDir, "revocation-applied").exists() }
                verifyRevokedTransportAndNewLogin(session, originalPending!!, queue)
                return
            }
            compose.waitUntil(60_000) { queue.orderQueue(session).singleOrNull()?.state == RecoveryState.ACTION_REQUIRED }
            val rejected = queue.orderQueue(session).single()
            check(rejected == originalPending!!.copy(state = RecoveryState.ACTION_REQUIRED))
            // A dependent confirmation cannot create a new key or resubmit an ACTION_REQUIRED record.
            compose.onNodeWithText("Confirmar pedido").performScrollTo().performClick()
            check(queue.orderQueue(session).single() == rejected)
            // Recovery is asynchronous: ACTION_REQUIRED in durable native storage is
            // authoritative. The immediate online catalog 409 uses a separate UI toast.
            // Do not require that online toast after the offline replay has been rejected.
            check(compose.onAllNodesWithText("Pedido confirmado pelo servidor.").fetchSemanticsNodes().isEmpty())
            return
        }
        if (fault) {
            compose.waitUntil(30_000) { compose.onAllNodesWithText("Pedido confirmado pelo servidor.").fetchSemanticsNodes().isEmpty() &&
                compose.onAllNodes(hasText("Um ou mais itens não podem mais ser confirmados.", substring = true)).fetchSemanticsNodes().isNotEmpty() }
            compose.onNodeWithTag("workspace-Pedido atual").assertExists()
            return
        }
        waitText("Pedido confirmado pelo servidor.")
        // Confirmation returns to the table list by design; reopen the original Tab.
        compose.waitUntil(30_000) { compose.onAllNodesWithText("Outras comandas", substring = true).fetchSemanticsNodes().isNotEmpty() }
        compose.onNode(hasText("Outras comandas", substring = true) and hasClickAction()).performClick()
        val originalTab = hasTestTag("other-tab-$originalTabId")
        compose.onNodeWithTag("tables-list").performScrollToNode(originalTab)
        compose.waitUntil(30_000) {
            compose.onAllNodes(originalTab and isEnabled()).fetchSemanticsNodes().size == 1
        }
        compose.onNode(originalTab).assertIsEnabled().performClick()
        // UX2 can expose the account as a page instead of the legacy workspace tab.
        compose.waitUntil(30_000) {
            compose.onAllNodesWithTag("workspace-Conta").fetchSemanticsNodes().isNotEmpty() ||
                compose.onAllNodes(hasText("Conta") and hasClickAction()).fetchSemanticsNodes().isNotEmpty()
        }
        if (compose.onAllNodesWithTag("workspace-Conta").fetchSemanticsNodes().isNotEmpty()) {
            compose.onNodeWithTag("workspace-Conta").performClick()
        } else {
            compose.onNode(hasText("Conta") and hasClickAction()).performClick()
        }
        compose.waitUntil(30_000) { compose.onAllNodesWithTag("account-balance").fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithTag("account-balance").assertIsDisplayed()
        compose.onNodeWithText("Saldo em aberto").assertIsDisplayed()
        val confirmed = operations.tabDetail(session.tokens.accessToken, originalTabId)
        check(confirmed.orders.size == 1) { "Expected exactly one canonical Order" }
        check(confirmed.summary.chargesCents == 1700L && confirmed.summary.exposureCents == 1700L)
        compose.onNode(hasText(formatCents(1700L)) and hasAnyAncestor(hasTestTag("account-balance")))
            .assertIsDisplayed()
        // Order creation originates only from real Compose actions; no seeded UI or optimistic confirmation.
    }
    private fun evidence(message: String) {
        InstrumentationRegistry.getInstrumentation().sendStatus(0, android.os.Bundle().apply {
            putString("stream", "\n$message\n")
        })
    }

    private fun verifyRevokedTransportAndNewLogin(session: StoredSession, original: RecoveryIntent.ConfirmOrder, queue: PendingMutationIntentStore) {
        val auth = AuthHttpClient(BuildConfig.RODADA_API_BASE_URL)
        fun denied(action: () -> Unit) {
            val deadline = android.os.SystemClock.elapsedRealtime() + 30_000
            while (true) {
                try { action(); error("Revoked credentials unexpectedly accepted") }
                catch (rejected: AuthApiException) { check(rejected.status in listOf(401, 403)); return }
                catch (transport: java.io.IOException) {
                    check(android.os.SystemClock.elapsedRealtime() < deadline) { "Emulator route never recovered" }
                    Thread.sleep(250)
                }
            }
        }
        denied { auth.me(session.tokens.accessToken) }
        denied { auth.refresh(session.tokens.refreshToken) }
        denied { OperationsHttpClient(BuildConfig.RODADA_API_BASE_URL).confirmOrder(session.tokens.accessToken, original.tabId,
            original.lines.map { CartLine(Product(it.productId, "Captured UI item", 0, true, "BAR", "AVAILABLE"), it.quantity, it.customization) }, original.idempotencyKey) }
        val stream = java.net.URL(BuildConfig.RODADA_API_BASE_URL + "realtime/stream/").openConnection() as java.net.HttpURLConnection
        try {
            stream.connectTimeout = 5000; stream.readTimeout = 5000
            stream.setRequestProperty("Authorization", "Bearer " + session.tokens.accessToken)
            check(stream.responseCode in listOf(401, 403))
        } finally { stream.disconnect() }
        check(queue.orderQueue(session).single().copy(state = original.state) == original)
        waitText("Estabelecimento")
        for ((label, value) in listOf("Estabelecimento" to "android-post-drop-ci", "Operador" to "android-post-drop-operator", "PIN" to "2468")) {
            compose.onNodeWithText(label).performTextClearance()
            compose.onNodeWithText(label).performTextInput(value)
        }
        compose.onNodeWithText("Entrar").performClick()
        compose.waitUntil(30_000) { compose.onAllNodes(hasTestTag("attendance-now") and isEnabled()).fetchSemanticsNodes().isNotEmpty() }
        val next = SecureSessionStore(InstrumentationRegistry.getInstrumentation().targetContext).load() ?: error("New login missing")
        check(next.sessionId != session.sessionId)
        check(queue.orderQueue(next).isEmpty())
        check(queue.blockedFor(next).any { it.id == original.id })
        val operations = OperationsHttpClient(BuildConfig.RODADA_API_BASE_URL)
        val foreign = auth.login(LoginRequest(venueSlug = "android-post-drop-foreign-ci", loginIdentifier = "android-post-drop-foreign-operator", pin = "2468", installationId = "issue106-native-foreign-" + java.util.UUID.randomUUID()))
        val foreignTab = InstrumentationRegistry.getArguments().getString("foreignTabId") ?: error("Missing foreign control Tab")
        check(operations.tabDetail(next.tokens.accessToken, original.tabId).summary.chargesCents == 0L)
        check(operations.tabDetail(foreign.tokens.accessToken, foreignTab).summary.chargesCents == 0L)
        fun foreignDenied(action: () -> Unit) {
            try { action(); error("Foreign Venue unexpectedly accepted") }
            catch (rejected: OperationsApiException) { check(rejected.status == 404) }
        }
        for ((token, tabId) in listOf(next.tokens.accessToken to foreignTab, foreign.tokens.accessToken to original.tabId)) {
            foreignDenied { operations.tabDetail(token, tabId) }
            foreignDenied { operations.confirmOrder(token, tabId, original.lines.map { CartLine(Product(it.productId, "Foreign denied", 0, true, "BAR", "AVAILABLE"), it.quantity, it.customization) }, java.util.UUID.randomUUID().toString()) }
        }
        // Native API ingress may not impersonate a tenant Host without the BFF assertion.
        val tenant = java.net.URL(BuildConfig.RODADA_API_BASE_URL + "auth/me/").openConnection() as java.net.HttpURLConnection
        try {
            tenant.connectTimeout = 5000; tenant.readTimeout = 5000
            tenant.setRequestProperty("Host", "issue106b-ci.rodada.bar")
            tenant.setRequestProperty("Authorization", "Bearer " + next.tokens.accessToken)
            check(tenant.responseCode == 403)
            val body = org.json.JSONObject(tenant.errorStream.bufferedReader().use { it.readText() })
            check(body.getString("code") == "HOST_ASSERTION_REQUIRED")
        } finally { tenant.disconnect() }
        evidence("NATIVE_VENUE_A_B_READ_POST_ISOLATED")
        val files = InstrumentationRegistry.getInstrumentation().targetContext.filesDir
        java.io.File(files, "expiry-session-id").writeText(foreign.sessionId)
        compose.waitUntil(60_000) { java.io.File(files, "expiry-applied").exists() }
        try { auth.me(foreign.tokens.accessToken); error("Expired access accepted") }
        catch (expired: AuthApiException) { check(expired.status == 401 && expired.code == "ACCESS_TOKEN_EXPIRED") }
        val refreshed = auth.refresh(foreign.tokens.refreshToken)
        check(refreshed.accessToken != foreign.tokens.accessToken)
        check(auth.me(refreshed.accessToken).venueId == foreign.venueId)
        evidence("NATIVE_EXPIRED_ACCESS_401_REFRESH_200")
        compose.onNodeWithTag("attendance-now").performClick()
        val pending = hasText("Pendências", substring = true) and hasClickAction()
        compose.waitUntil(30_000) { compose.onAllNodes(pending).fetchSemanticsNodes().isNotEmpty() }
        compose.onNode(pending).performClick()
        compose.waitUntil(30_000) { compose.onAllNodes(hasText("outra sessão", substring = true, ignoreCase = true)).fetchSemanticsNodes().isNotEmpty() }
        evidence("NATIVE_REVOKED_GET_POST_REFRESH_SSE_DENIED; NEW_LOGIN_REVIEW_ONLY")
    }

}
