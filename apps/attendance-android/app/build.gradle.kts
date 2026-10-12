import java.net.URI

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
}

// Development and Play release configuration deliberately do not share a default API.
// A release without an explicit HTTPS endpoint and a real upload keystore fails closed.
val debugApiUrl = providers.gradleProperty("rodadaApiBaseUrl").getOrElse("http://10.0.2.2:8000/")
val releaseApiUrl = providers.gradleProperty("rodadaReleaseApiBaseUrl")
    .orElse(providers.environmentVariable("RODADA_RELEASE_API_BASE_URL"))
    .getOrElse("").trim()
val uploadKeystoreFile = providers.gradleProperty("rodadaUploadStoreFile")
    .orElse(providers.environmentVariable("RODADA_UPLOAD_KEYSTORE_FILE")).orNull
val uploadStorePassword = providers.gradleProperty("rodadaUploadStorePassword")
    .orElse(providers.environmentVariable("RODADA_UPLOAD_STORE_PASSWORD")).orNull
val uploadKeyAlias = providers.gradleProperty("rodadaUploadKeyAlias")
    .orElse(providers.environmentVariable("RODADA_UPLOAD_KEY_ALIAS")).orNull
val uploadKeyPassword = providers.gradleProperty("rodadaUploadKeyPassword")
    .orElse(providers.environmentVariable("RODADA_UPLOAD_KEY_PASSWORD")).orNull

fun asBuildConfigString(value: String): String =
    "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"") + "\""

android {
    namespace = "com.rodada.attendance"
    compileSdk = 37

    defaultConfig {
        // This ID is permanent after the first Play upload. Do not change casually.
        applicationId = "com.rodada.attendance"
        minSdk = if (providers.gradleProperty("sumupSdk").orNull == "true") 30 else 26
        targetSdk = 37
        versionCode = providers.gradleProperty("rodadaVersionCode").getOrElse("1").toInt()
        versionName = providers.gradleProperty("rodadaVersionName").getOrElse("0.1.0")

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    signingConfigs {
        if (listOf(uploadKeystoreFile, uploadStorePassword, uploadKeyAlias, uploadKeyPassword)
                .all { !it.isNullOrBlank() }
        ) {
            create("playUpload") {
                storeFile = file(requireNotNull(uploadKeystoreFile))
                storePassword = uploadStorePassword
                keyAlias = uploadKeyAlias
                keyPassword = uploadKeyPassword
            }
        }
    }

    buildTypes {
        getByName("debug") {
            buildConfigField("String", "RODADA_API_BASE_URL", asBuildConfigString(debugApiUrl))
        }
        getByName("release") {
            isDebuggable = false
            // Enable shrinking only after testing the authenticated networking/JSON flows with R8.
            isMinifyEnabled = false
            buildConfigField("String", "RODADA_API_BASE_URL", asBuildConfigString(releaseApiUrl))
            signingConfig = signingConfigs.findByName("playUpload")
        }
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    compileOptions {
        isCoreLibraryDesugaringEnabled = providers.gradleProperty("sumupSdk").orNull == "true"
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

// A checked-in or mistakenly cached localhost URL must NEVER become a Play release.
// Keep validation attached to both AAB and APK release entrypoints.
val verifyPlayRelease by tasks.registering {
    group = "verification"
    description = "Check HTTPS endpoint, release version and upload signing before packaging."
    doLast {
        val parsed = runCatching { URI(releaseApiUrl) }.getOrNull()
        val host = parsed?.host?.lowercase().orEmpty()
        check(parsed?.scheme.equals("https", ignoreCase = true) &&
            host.isNotBlank() &&
            host !in setOf("localhost", "127.0.0.1", "10.0.2.2", "0.0.0.0") &&
            !host.endsWith(".localhost") && !host.endsWith(".invalid") &&
            parsed?.userInfo == null && parsed?.rawQuery == null &&
            parsed?.rawFragment == null && parsed?.port in listOf(-1, 443)
        ) { "Play release requires RODADA_RELEASE_API_BASE_URL to be a real HTTPS API origin." }
        check(listOf(uploadKeystoreFile, uploadStorePassword, uploadKeyAlias, uploadKeyPassword)
            .all { !it.isNullOrBlank() }
        ) { "Play release requires all four RODADA_UPLOAD_* signing variables." }
        check(file(requireNotNull(uploadKeystoreFile)).isFile) {
            "RODADA_UPLOAD_KEYSTORE_FILE does not point to an existing keystore."
        }
        val code = providers.gradleProperty("rodadaVersionCode").getOrElse("1").toInt()
        check(code > 0) { "rodadaVersionCode must be positive." }
    }
}
tasks.matching { it.name in setOf("bundleRelease", "assembleRelease", "packageReleaseBundle") }
    .configureEach { dependsOn(verifyPlayRelease) }

dependencies {
    if (providers.gradleProperty("sumupSdk").orNull == "true") {
        implementation("com.sumup.tap-to-pay:utopia-sdk:1.1.6")
        coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.5")
    }

    val composeBom = platform("androidx.compose:compose-bom:2026.09.00")

    implementation(composeBom)
    implementation("androidx.activity:activity-compose:1.13.0")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.11.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.11.0")

    debugImplementation(composeBom)
    debugImplementation("androidx.compose.ui:ui-tooling")

    androidTestImplementation(composeBom)
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    androidTestImplementation("androidx.test:runner:1.7.0")
    androidTestImplementation("androidx.test.ext:junit:1.3.0")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
    testImplementation("junit:junit:4.13.2")
    // Android supplies org.json on devices, while local JVM tests otherwise receive a stub.
    testImplementation("org.json:json:20250517")
}
