package com.rodada.attendance.auth

/** Synchronous HTTP calls run inside withAuthorizedAccess on one IO thread. */
object OriginatingSessionContext {
    val id = ThreadLocal<String>()
}
