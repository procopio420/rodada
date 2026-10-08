package com.rodada.attendance.realtime

import org.junit.Assert.*
import org.junit.Test

class RealtimeProtocolTest {
    @Test fun duplicateAndReorderedCursorsDoNotRepeatInvalidation() {
        val gate = CursorGate()
        assertTrue(gate.accept("venue:12"))
        assertFalse(gate.accept("venue:12"))
        assertFalse(gate.accept("venue:11"))
        assertTrue(gate.accept("venue:14"))
        assertEquals("venue:14", gate.cursor)
        gate.reset("venue:30")
        assertFalse(gate.accept("venue:29"))
        assertTrue(gate.accept("venue:31"))
    }
    @Test fun delayedFramesCommentsAndMultilineDataAreParsed() {
        val parser = SseFrames()
        assertNull(parser.line(": keepalive"))
        assertNull(parser.line("event: change"))
        assertNull(parser.line("id: venue:42"))
        assertNull(parser.line("data: {"))
        assertNull(parser.line("data: }"))
        assertEquals(SseFrame("change", "venue:42", "{\n}"), parser.line(""))
        assertNull(parser.line(""))
    }
    @Test fun resetAndReadyNeverBecomeDomainCommands() {
        val parser = SseFrames()
        parser.line("event: reset")
        parser.line("data: {\"reason\":\"expired\"}")
        assertEquals("reset", parser.line("")?.event)
        parser.line("event: ready")
        parser.line("data: {\"cursor\":\"venue:50\"}")
        assertEquals("ready", parser.line("")?.event)
    }
}
