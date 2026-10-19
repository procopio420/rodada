package com.rodada.attendance.operations

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.async
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test
import java.io.IOException

class SessionActionTest {
    /** A deterministic transport fake; release controls completion after the session switch. */
    private class SuspendedRepository {
        val started = CompletableDeferred<Unit>()
        val response = CompletableDeferred<Unit>()
        suspend fun command() { started.complete(Unit); response.await() }
    }

    @Test fun `late X failure cannot become B pending command and B tap Y stays Y`() = runBlocking {
        val fence = FinancialResponseFence()
        var session = "A"
        val guard = fence.capture({ session == "A" })
        val repository = SuspendedRepository()
        var pending: ServiceRequestAction? = null
        var submitting = true
        var error: Throwable? = null
        val original = ServiceRequestAction("X", false, "A")
        val job = async {
            runSessionAction(guard, {
                try { awaitCurrent { repository.command() }; pending = null }
                catch (failure: Exception) { check(); pending = original; throw failure }
            }, { submitting = false }, { submitting = false; error = it })
        }
        repository.started.await()
        session = "B"; fence.invalidate()
        // B's new action is busy before the old callback is released.
        submitting = true
        repository.response.completeExceptionally(IOException("A transport failed"))
        job.await()
        assertNull(pending); assertNull(error); assertTrue(submitting)
        val selected = serviceRequestActionForSession(pending, "B", "Y", true)
        assertEquals(ServiceRequestAction("Y", true, "B"), selected)
        // Even a retained foreign/legacy record must never override the selected task.
        assertEquals(selected, serviceRequestActionForSession(original, "B", "Y", true))
        assertEquals(selected, serviceRequestActionForSession(ServiceRequestAction("X", false), "B", "Y", true))
        assertEquals(original, serviceRequestActionForSession(original, "A", "Y", true))
    }

    @Test fun `old success and rejection preserve durable intent and new busy state across A B and A B A`() = runBlocking {
        for (returnToA in listOf(false, true)) for (failure in listOf(false, true)) {
            val fence = FinancialResponseFence()
            var session = "A"
            val guard = fence.capture({ session == "A" })
            val repository = SuspendedRepository()
            var durableIntent = "original-A"
            var presentation = "A"
            var submitting = true
            var callbacks = 0
            val job = async {
                runSessionAction(guard, {
                    try { awaitCurrent { repository.command() } }
                    catch (rejection: Exception) { check(); durableIntent = "removed-on-rejection"; throw rejection }
                    durableIntent = "removed-on-success"
                    presentation = "old-result"
                }, { submitting = false; callbacks++ }, { submitting = false; callbacks++ })
            }
            repository.started.await()
            session = "B"; fence.invalidate()
            if (returnToA) { session = "A"; fence.invalidate() }
            presentation = "new-$session"; submitting = true
            if (failure) repository.response.completeExceptionally(IllegalStateException("late rejection"))
            else repository.response.complete(Unit)
            job.await()
            assertEquals("original-A", durableIntent)
            assertEquals("new-$session", presentation)
            assertTrue(submitting); assertEquals(0, callbacks)
        }
    }

    @Test fun `current action publishes outcome and releases busy state`() = runBlocking {
        for (failure in listOf(false, true)) {
            val guard = FinancialResponseFence().capture({ true })
            var success = 0; var errors = 0; var submitting = true
            runSessionAction(guard, { awaitCurrent { if (failure) throw IOException("current failure") } },
                { success++; submitting = false }, { errors++; submitting = false })
            assertFalse(submitting)
            assertEquals(if (failure) 0 else 1, success)
            assertEquals(if (failure) 1 else 0, errors)
        }
    }

    @Test fun `invalidated action never starts transport nor invokes outcome callbacks`() = runBlocking {
        val fence = FinancialResponseFence()
        val guard = fence.capture({ true })
        fence.invalidate()
        var requests = 0
        var callbacks = 0
        runSessionAction(guard, { awaitCurrent { requests++ } }, { callbacks++ }, { callbacks++ })
        assertEquals(0, requests)
        assertEquals(0, callbacks)
    }

    @Test fun `switch between reads prevents second request and canonical publication`() = runBlocking {
        val fence = FinancialResponseFence()
        val guard = fence.capture({ true })
        var requests = 0
        var published = false
        runSessionAction(guard, {
            awaitCurrent { requests++; fence.invalidate() }
            awaitCurrent { requests++ }
            published = true
        }, { fail("Stale completion") }, { fail("Stale error") })
        assertEquals(1, requests)
        assertFalse(published)
    }

}
