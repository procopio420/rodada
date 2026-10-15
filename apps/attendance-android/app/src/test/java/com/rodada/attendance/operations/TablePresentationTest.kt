package com.rodada.attendance.operations

import com.rodada.attendance.ui.RodadaVisual
import org.junit.Assert.assertEquals
import org.junit.Test

class TablePresentationTest {
    @Test fun tableStatusesUseSharedSemanticColors() {
        assertEquals(RodadaVisual.Success, tableStatusColor("AVAILABLE"))
        assertEquals(RodadaVisual.Info, tableStatusColor("OCCUPIED"))
        assertEquals(RodadaVisual.Amber, tableStatusColor("DIRTY"))
        assertEquals(RodadaVisual.Amber, tableStatusColor("CLEANING"))
        assertEquals(RodadaVisual.Danger, tableStatusColor("OUT_OF_SERVICE"))
        assertEquals(RodadaVisual.Muted, tableStatusColor("UNKNOWN"))
    }
}
