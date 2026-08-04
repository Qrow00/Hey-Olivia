package com.jarvis.jarvis_app

import android.content.Context
import android.os.Build
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel

class HealthBridgePlugin(private val context: Context) {

    fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        when (call.method) {
            "isAvailable" -> {
                result.success(Build.VERSION.SDK_INT >= 34)
            }
            "requestPermissions" -> {
                result.success(true)
            }
            "readMetrics" -> {
                result.success(mapOf(
                    "heart_rate" to 0.0,
                    "steps" to 0,
                    "spo2" to 0.0,
                    "sleep_hours" to 0.0,
                    "calories" to 0.0,
                    "period_hours" to (call.argument<Int>("hours") ?: 24),
                ))
            }
            else -> result.notImplemented()
        }
    }
}
