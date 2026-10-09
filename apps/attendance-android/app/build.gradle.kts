plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "com.rodada.attendance"
    compileSdk = 37

    defaultConfig {
        applicationId = "com.rodada.attendance"
        minSdk = if (providers.gradleProperty("sumupSdk").orNull == "true") 30 else 26
        targetSdk = 37
        versionCode = 1
        versionName = "0.1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        buildConfigField(
            "String",
            "RODADA_API_BASE_URL",
            "\"http://10.0.2.2:8000/\"",
        )
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
    debugImplementation("androidx.compose.ui:ui-test-manifest")
    testImplementation("junit:junit:4.13.2")
    // Android supplies org.json on devices, while local JVM tests otherwise receive a stub.
    testImplementation("org.json:json:20250517")
}
