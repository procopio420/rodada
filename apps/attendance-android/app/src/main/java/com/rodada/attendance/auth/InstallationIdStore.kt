package com.rodada.attendance.auth

import android.content.Context
import java.util.UUID

class InstallationIdStore(context: Context) {
    private val preferences =
        context.getSharedPreferences("rodada_installation", Context.MODE_PRIVATE)

    fun getOrCreate(): String {
        val existing = preferences.getString(KEY_INSTALLATION_ID, null)
        if (!existing.isNullOrBlank()) return existing

        val created = UUID.randomUUID().toString()
        preferences.edit().putString(KEY_INSTALLATION_ID, created).apply()
        return created
    }

    private companion object {
        const val KEY_INSTALLATION_ID = "installation_id"
    }
}
