package com.jarvis.jarvis_app

import android.Manifest
import android.app.Activity
import android.content.Context
import android.content.pm.PackageManager
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.os.Handler
import android.os.Looper
import io.flutter.plugin.common.EventChannel
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import java.lang.ref.WeakReference
import kotlin.concurrent.thread

class MicRecorderPlugin(
    private val context: Context,
    private val activityRef: WeakReference<Activity>,
) : MethodChannel.MethodCallHandler, EventChannel.StreamHandler {

    companion object {
        private const val SAMPLE_RATE = 16000
        private const val CHUNK_BYTES = 4096
        private const val REQUEST_CODE = 2002
    }

    private val mainHandler = Handler(Looper.getMainLooper())

    private var audioRecord: AudioRecord? = null
    private var recording = false
    private var worker: Thread? = null
    private var sink: EventChannel.EventSink? = null
    private var pendingStart: MethodChannel.Result? = null

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        when (call.method) {
            "start" -> handleStart(result)
            "stop" -> {
                stopRecording()
                result.success(true)
            }
            else -> result.notImplemented()
        }
    }

    private fun handleStart(result: MethodChannel.Result) {
        if (recording) {
            result.success(true)
            return
        }
        val activity = activityRef.get()
        if (activity == null || activity.isFinishing || activity.isDestroyed) {
            result.error("NO_ACTIVITY", "Activity not available", null)
            return
        }
        val granted = activity.checkSelfPermission(Manifest.permission.RECORD_AUDIO) ==
            PackageManager.PERMISSION_GRANTED
        if (!granted) {
            pendingStart = result
            activity.requestPermissions(arrayOf(Manifest.permission.RECORD_AUDIO), REQUEST_CODE)
        } else if (startRecording()) {
            result.success(true)
        } else {
            result.error("START_FAILED", "Failed to start AudioRecord", null)
        }
    }

    fun onRequestPermissionsResult(requestCode: Int, grantResults: IntArray) {
        if (requestCode != REQUEST_CODE) return
        val result = pendingStart
        pendingStart = null
        if (result == null) return
        val granted = grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED
        if (granted) {
            if (startRecording()) result.success(true)
            else result.error("START_FAILED", "Failed to start AudioRecord", null)
        } else {
            result.error("PERMISSION_DENIED", "Microphone permission required", null)
        }
    }

    private fun startRecording(): Boolean {
        val minBuf = AudioRecord.getMinBufferSize(
            SAMPLE_RATE,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
        )
        if (minBuf <= 0) return false
        val bufferSize = maxOf(minBuf, CHUNK_BYTES * 4)

        val record = try {
            AudioRecord(
                MediaRecorder.AudioSource.VOICE_RECOGNITION,
                SAMPLE_RATE,
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT,
                bufferSize,
            )
        } catch (_: Exception) {
            return false
        }
        if (record.state != AudioRecord.STATE_INITIALIZED) {
            record.release()
            return false
        }

        audioRecord = record
        recording = true
        worker = thread(name = "mic-recorder", isDaemon = true) {
            val buf = ByteArray(CHUNK_BYTES)
            try {
                record.startRecording()
                while (recording && !Thread.currentThread().isInterrupted) {
                    val read = record.read(buf, 0, buf.size)
                    if (read > 0) {
                        val chunk = buf.copyOf(read)
                        mainHandler.post { sink?.success(chunk) }
                    }
                }
            } catch (_: Exception) {
            } finally {
                try {
                    record.stop()
                } catch (_: Exception) {}
                record.release()
                if (audioRecord === record) audioRecord = null
            }
        }
        return true
    }

    private fun stopRecording() {
        recording = false
        worker?.interrupt()
        worker?.join(2000)
        worker = null
        val pending = pendingStart
        if (pending != null) {
            pendingStart = null
            pending.error("STOPPED", "Recording stopped before permission result", null)
        }
        audioRecord?.let { rec ->
            try {
                rec.stop()
            } catch (_: Exception) {}
            rec.release()
        }
        audioRecord = null
        sink = null
    }

    override fun onListen(arguments: Any?, events: EventChannel.EventSink?) {
        sink = events
    }

    override fun onCancel(arguments: Any?) {
        sink = null
    }
}
