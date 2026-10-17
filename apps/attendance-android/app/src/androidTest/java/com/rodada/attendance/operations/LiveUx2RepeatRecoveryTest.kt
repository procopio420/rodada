package com.rodada.attendance.operations

import androidx.compose.material3.Surface
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import com.rodada.attendance.BuildConfig
import com.rodada.attendance.auth.*
import com.rodada.attendance.corrections.CorrectionsRepository
import com.rodada.attendance.refunds.RefundsRepository
import com.rodada.attendance.ui.RodadaTheme
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import java.net.HttpURLConnection
import java.net.URL
import java.util.UUID

/** Opt-in disposable TCP-reset regression; production UI, VM, repositories and Django/PostgreSQL. */
class LiveUx2RepeatRecoveryTest {
    @get:Rule val compose = createComposeRule()

    @Test fun lostRepeatAckWithEmptyCartVerifiesOriginalIntent() {
        val args = InstrumentationRegistry.getArguments()
        assumeTrue("Explicit disposable TCP-reset runner only", args.getString("liveUx2Repeat") == "true")
        val upstream = requireNotNull(args.getString("upstreamUrl"))
        check(upstream.matches(Regex("""http://10\.0\.2\.2:[0-9]{4,5}/""")))
        check(BuildConfig.RODADA_API_BASE_URL == "http://10.0.2.2:18131/")
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val session = AuthHttpClient(upstream).login(LoginRequest("android-post-drop-ci", "android-post-drop-operator", "2468", "ux2-repeat-" + UUID.randomUUID()))
        SecureSessionStore(context).save(session)
        val api = OperationsHttpClient(upstream)
        val product = api.products(session.tokens.accessToken).first { it.active && it.availability == "AVAILABLE" && it.priceCents in 1..1000 && it.variants.isEmpty() && it.modifierGroups.isEmpty() }
        val opened = api.openTab(session.tokens.accessToken, "UX2 repeat recovery " + UUID.randomUUID().toString().take(8))
        api.confirmOrder(session.tokens.accessToken, opened.id, listOf(CartLine(product, 1)), UUID.randomUUID().toString())
        val before = api.tabDetail(session.tokens.accessToken, opened.id)
        assertEquals(1, before.orders.size)
        assertNotNull(before.orders.single().items.single().fulfillmentStationSnapshot)
        val auth = AuthRepository(context)
        val queue = PendingMutationIntentStore(context)
        lateinit var vm: OperationsViewModel
        compose.runOnUiThread {
            vm = OperationsViewModel(OperationsRepository(auth), queue, auth, CorrectionsRepository(auth), RefundsRepository(auth))
            vm.ensureLoaded(session)
            vm.startRealtime(session)
        }
        compose.waitUntil(30_000) { vm.state.connectivity == ConnectivityState.ONLINE && !vm.state.loading }
        compose.runOnUiThread { vm.stopRealtime(); vm.selectTab(session, opened.id) }
        compose.waitUntil(30_000) { vm.state.selectedTab?.summary?.id == opened.id && !vm.state.loading && !vm.state.submitting }
        compose.setContent { RodadaTheme { Surface {
            vm.state.selectedTab?.let { tab -> TabWorkspace(vm.state, tab, {}, { p, c -> vm.addProduct(p, c) }, { id, c -> vm.editCartLine(id, c) }, { id, delta -> vm.changeCartQuantity(id, delta) }, { vm.confirmOrder(session) },
                {}, {}, {}, {}, {}, {}, {}, {}, onRepeatOrder = { review, quantities -> vm.repeatOrder(session, tab.summary.id, review, quantities) }, onVerifyPending = { vm.revalidateConnection(session) }) }
        } } }
        compose.onNodeWithText("↻ Mais uma rodada").performScrollTo().performClick()
        compose.onNode(hasText("Confirmar e enviar ·", substring = true) and hasClickAction()).performClick()
        compose.waitUntil(45_000) { !vm.state.submitting && queue.orderQueue(session).singleOrNull()?.state == RecoveryState.CHECKING }
        val original = queue.orderQueue(session).single()
        assertFalse(original.clearCartOnConfirmation)
        assertTrue(vm.state.cart.isEmpty())
        assertEquals(original.idempotencyKey, vm.state.orderIntentId)
        val afterCommit = api.tabDetail(session.tokens.accessToken, opened.id)
        assertEquals(2, afterCommit.orders.size)
        captureCriticalEvidence(compose, "ux2-repeat-unknown-empty-cart", compose.onRoot())
        val disarm = URL(BuildConfig.RODADA_API_BASE_URL + "__fault/disarm").openConnection() as HttpURLConnection
        disarm.requestMethod = "POST"
        disarm.doOutput = true
        disarm.setFixedLengthStreamingMode(0)
        disarm.outputStream.close()
        assertEquals(200, disarm.responseCode)
        disarm.inputStream.close()
        disarm.disconnect()
        compose.onNodeWithText("Verificar mesmo pedido").performScrollTo().performClick()
        compose.waitUntil(45_000) { queue.orderQueue(session).isEmpty() && vm.state.orderIntentId == null && !vm.state.submitting }
        val canonical = api.tabDetail(session.tokens.accessToken, opened.id)
        assertEquals(2, canonical.orders.size)
        assertEquals(afterCommit.summary.chargesCents, canonical.summary.chargesCents)
        assertTrue(vm.state.cart.isEmpty())
        captureCriticalEvidence(compose, "ux2-repeat-reconciled-empty-cart", compose.onRoot())
        val proof = org.json.JSONObject().put("tab_id", opened.id).put("idempotency_key", original.idempotencyKey).put("intent_id", original.id).put("clear_cart_on_confirmation", original.clearCartOnConfirmation)
            .put("before_orders", before.orders.size).put("after_commit_orders", afterCommit.orders.size).put("after_verify_orders", canonical.orders.size).put("charges_cents", canonical.summary.chargesCents)
        java.io.File(context.filesDir, "ux2-repeat-recovery-proof.json").writeText(proof.toString())
        compose.runOnUiThread { vm.stopRealtime(); vm.pauseOrderRecovery() }
    }
}
