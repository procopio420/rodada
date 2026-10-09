pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        if (providers.gradleProperty("sumupSdk").orNull == "true") {
            maven { url = uri("https://maven.sumup.com/releases") }
            maven {
                url = uri("https://tap-to-pay-sdk.fleet.live.sumup.net/")
                credentials {
                    username = providers.environmentVariable("SUMUP_MAVEN_USER").orNull
                    password = providers.environmentVariable("SUMUP_MAVEN_PASSWORD").orNull
                }
                content { includeGroup("com.sumup.tap-to-pay") }
            }
        }
    }
}

rootProject.name = "RodadaAttendance"
include(":app")
