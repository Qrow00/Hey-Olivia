package com.jarvis.jarvis_app

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.media.projection.MediaProjectionManager
import android.os.Build
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.EventChannel
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {

    private val SCREEN_CAPTURE_CHANNEL = "screen_capture"
    private val HEALTH_BRIDGE_CHANNEL = "health_bridge"
    private val TTS_CHANNEL = "tts_plugin"
    private val MIC_RECORDER_CHANNEL = "mic_recorder"
    private val MIC_RECORDER_EVENTS = "mic_recorder_events"
    private val SCREEN_CAPTURE_REQUEST = 1001
    private var resultCallback: MethodChannel.Result? = null
    private var healthBridge: HealthBridgePlugin? = null
    private var ttsPlugin: TTSPlugin? = null
    private var micRecorderPlugin: MicRecorderPlugin? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            SCREEN_CAPTURE_CHANNEL
        ).setMethodCallHandler { call, result ->
            when (call.method) {
                "captureFrame" -> {
                    val service = ScreenCaptureService.instance
                    if (service != null) {
                        service.setOnFrameCapturedListener { base64 ->
                            runOnUiThread {
                                result.success(base64.toByteArray())
                            }
                        }
                        result.success(null)
                    } else {
                        result.error("NO_SERVICE", "Screen capture service not running", null)
                    }
                }
                "startCapture" -> {
                    val width = call.argument<Int>("width") ?: 720
                    val height = call.argument<Int>("height") ?: 1280
                    val fps = call.argument<Int>("fps") ?: 5
                    startScreenCapture(width, height, fps, result)
                }
                "stopCapture" -> {
                    val intent = Intent(this, ScreenCaptureService::class.java).apply {
                        action = "STOP_CAPTURE"
                    }
                    startService(intent)
                    result.success(true)
                }
                "isCapturing" -> {
                    result.success(ScreenCaptureService.instance != null)
                }
                else -> {
                    result.notImplemented()
                }
            }
        }

        healthBridge = HealthBridgePlugin(this)
        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            HEALTH_BRIDGE_CHANNEL
        ).setMethodCallHandler { call, result ->
            healthBridge?.onMethodCall(call, result)
        }

        ttsPlugin = TTSPlugin(this)
        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            TTS_CHANNEL
        ).setMethodCallHandler { call, result ->
            ttsPlugin?.onMethodCall(call, result)
        }

        micRecorderPlugin = MicRecorderPlugin(this, java.lang.ref.WeakReference(this))
        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            MIC_RECORDER_CHANNEL
        ).setMethodCallHandler { call, result ->
            micRecorderPlugin?.onMethodCall(call, result)
        }
        EventChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            MIC_RECORDER_EVENTS
        ).setStreamHandler(micRecorderPlugin)
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray,
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        micRecorderPlugin?.onRequestPermissionsResult(requestCode, grantResults)
    }

    private fun startScreenCapture(width: Int, height: Int, fps: Int, result: MethodChannel.Result) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            val projectionManager = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
            @Suppress("DEPRECATION")
            startActivityForResult(
                projectionManager.createScreenCaptureIntent(),
                SCREEN_CAPTURE_REQUEST
            )
            resultCallback = result
            pendingWidth = width
            pendingHeight = height
            pendingFps = fps
        } else {
            result.error("UNSUPPORTED", "Screen capture requires Android 5.0+", null)
        }
    }

    private var pendingWidth = 720
    private var pendingHeight = 1280
    private var pendingFps = 5

    @Suppress("DEPRECATION")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)

        if (requestCode == SCREEN_CAPTURE_REQUEST) {
            if (resultCode == Activity.RESULT_OK && data != null) {
                val intent = Intent(this, ScreenCaptureService::class.java).apply {
                    action = "START_CAPTURE"
                    putExtra("resultCode", resultCode)
                    putExtra("data", data)
                    putExtra("width", pendingWidth)
                    putExtra("height", pendingHeight)
                    putExtra("fps", pendingFps)
                }

                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    startForegroundService(intent)
                } else {
                    startService(intent)
                }

                resultCallback?.success(true)
            } else {
                resultCallback?.error("CANCELLED", "Screen capture permission denied", null)
            }
            resultCallback = null
        }
    }
}
