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
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import java.util.UUID

/** Opt-in only: HTTP/PG fixture seeded by Web E2E on an isolated loopback port. */
class LiveSpendingLimitModeTest {
    @get:Rule val compose = createComposeRule()
    @Test fun canonicalWarnAllowsExcessAndEnforceRestoresBlockWithoutChangingOrder() {
        assumeTrue(InstrumentationRegistry.getArguments().getString("liveSpendingMode") == "true")
        check(BuildConfig.RODADA_API_BASE_URL == "http://10.0.2.2:18144/")
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val authClient = AuthHttpClient(BuildConfig.RODADA_API_BASE_URL)
        val session = authClient.login(LoginRequest("web-e2e", "test-manager", "2468", "spending-" + UUID.randomUUID()))
        SecureSessionStore(context).save(session)
        val api = OperationsHttpClient(BuildConfig.RODADA_API_BASE_URL)
        fun policy() = api.request("GET", "/house-account/enforcement/", accessToken = session.tokens.accessToken)
        fun mode(value: String) {
            authClient.reauthenticate(session.tokens.accessToken, "2468")
            api.request("PUT", "/house-account/enforcement/", JSONObject()
                .put("mode", value).put("expected_version", policy().getInt("version"))
                .put("reason", "Synthetic native mode rehearsal").put("idempotency_key", UUID.randomUUID().toString())
                .put("expected_venue_id", session.venueId).put("expected_session_id", session.sessionId), session.tokens.accessToken)
        }
        val product = api.products(session.tokens.accessToken).single { it.name == "Bar E2E item" }
        val tab = api.openTab(session.tokens.accessToken, "Native mode " + UUID.randomUUID())
        val auth = AuthRepository(context)
        lateinit var model: OperationsViewModel
        mode("WARN_ONLY")
        try {
            compose.runOnUiThread {
                model = OperationsViewModel(OperationsRepository(auth), PendingMutationIntentStore(context), auth, CorrectionsRepository(auth), RefundsRepository(auth))
                model.ensureLoaded(session)
            }
            compose.waitUntil(30_000) { !model.state.loading }
            compose.runOnUiThread { model.selectTab(session, tab.id) }
            compose.waitUntil(30_000) { model.state.selectedTab?.summary?.id == tab.id && !model.state.loading }
            assertEquals("WARN_ONLY", model.state.selectedTab!!.summary.spendingLimitMode)
            compose.runOnUiThread { model.addProduct(product, quantity = 8) }
            compose.setContent { RodadaTheme { Surface {
                model.state.selectedTab?.let { selected ->
                    Ux2TabPages(model.state, selected, "Pedido atual", {}, {}, { _, _ -> }, { _, _ -> }, { _, _ -> },
                        { model.confirmOrder(session) }, { _, _ -> }, {})
                }
            } } }
            compose.onNodeWithText("Enviar 8 itens · ${formatCents(4000)}").assertIsEnabled().performClick()
            compose.waitUntil(30_000) { !model.state.submitting && model.state.selectedTab?.orders?.size == 1 }
            val confirmed = api.tabDetail(session.tokens.accessToken, tab.id)
            assertEquals(4000L, confirmed.summary.exposureCents)
            assertEquals(1, confirmed.orders.size)
            mode("ENFORCE")
            compose.runOnUiThread { model.refresh(session) }
            compose.waitUntil(30_000) { model.state.selectedTab?.summary?.spendingLimitMode == "ENFORCE" }
            compose.runOnUiThread { model.addProduct(product) }
            compose.onNodeWithText("Enviar 1 item · ${formatCents(500)}").assertIsNotEnabled()
            val final = api.tabDetail(session.tokens.accessToken, tab.id)
            assertEquals(confirmed.orders.single().id, final.orders.single().id)
            assertEquals(4000L, final.summary.exposureCents)
        } finally { if (policy().getString("mode") != "ENFORCE") mode("ENFORCE") }
    }
}
