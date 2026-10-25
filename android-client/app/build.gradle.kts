plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}


android {
    namespace = "ru.monitoring.mobile"
    compileSdk = 34

    defaultConfig {
        // Идентификатор пакета зафиксирован в том виде, в каком приложение уже
        // установлено у пользователей (бывший flavor `compactOps`). Менять нельзя:
        // другой applicationId — это другое приложение, обновление поверх и
        // сохранённые токен/настройки потеряются.
        applicationId = "ru.monitoring.mobile.compactops"
        minSdk = 26
        targetSdk = 34
        versionCode = providers.gradleProperty("ANDROID_VERSION_CODE").get().toInt()
        versionName = providers.gradleProperty("ANDROID_VERSION_NAME").get()

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables {
            useSupportLibrary = true
        }
        // Единственный интерфейс — Compact Ops Hub (flavor `legacy` удалён в 9.0.0).
        buildConfigField("boolean", "IS_COMPACT_OPS_HUB", "true")
    }

    // Подпись release-сборки. Все выпущенные APK подписаны debug-ключом ПК
    // разработчика, поэтому для бесшовного обновления у пользователей тем же
    // ключом подписывается и release. Путь/пароли задаются вне репозитория
    // (~/.gradle/gradle.properties или android-client/local.properties):
    //   COMDONE_KEYSTORE_FILE=C:/keys/comdone.keystore
    //   COMDONE_KEYSTORE_PASSWORD=android
    //   COMDONE_KEY_ALIAS=androiddebugkey
    //   COMDONE_KEY_PASSWORD=android
    // Без этих свойств используется стандартный ~/.android/debug.keystore.
    val localProps = java.util.Properties().apply {
        val file = rootProject.file("local.properties")
        if (file.exists()) file.inputStream().use { load(it) }
    }
    fun signingProp(name: String): String? =
        (providers.gradleProperty(name).orNull ?: localProps.getProperty(name))
            ?.takeIf { it.isNotBlank() }

    signingConfigs {
        create("release") {
            val keystore = signingProp("COMDONE_KEYSTORE_FILE")
            if (keystore != null) {
                storeFile = file(keystore)
                storePassword = signingProp("COMDONE_KEYSTORE_PASSWORD") ?: "android"
                keyAlias = signingProp("COMDONE_KEY_ALIAS") ?: "androiddebugkey"
                keyPassword = signingProp("COMDONE_KEY_PASSWORD") ?: "android"
            } else {
                initWith(getByName("debug"))
            }
        }
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    // Имя APK: ComDone-<версия>.apk (release) / ComDone-<версия>-debug.apk.
    applicationVariants.all {
        val variant = this
        outputs.all {
            val suffix = if (variant.buildType.name == "release") "" else "-${variant.buildType.name}"
            (this as com.android.build.gradle.internal.api.BaseVariantOutputImpl).outputFileName =
                "ComDone-${variant.versionName}$suffix.apk"
        }
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}


dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.06.00")

    implementation(composeBom)
    androidTestImplementation(composeBom)

    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.3")
    implementation("androidx.activity:activity-compose:1.9.0")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material:material")
    implementation("androidx.compose.material3:material3:1.2.1")
    implementation("com.google.android.material:material:1.12.0")
    implementation("androidx.compose.material:material-icons-extended:1.6.8")

    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.3")

    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.squareup.retrofit2:converter-moshi:2.11.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")
    implementation("com.squareup.moshi:moshi-kotlin:1.15.1")

    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1")
    implementation("androidx.work:work-runtime-ktx:2.9.1")

    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.6.1")
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
