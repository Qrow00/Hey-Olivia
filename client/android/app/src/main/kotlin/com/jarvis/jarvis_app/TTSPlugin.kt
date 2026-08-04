package com.jarvis.jarvis_app

import android.content.Context
import android.media.MediaPlayer
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import java.io.File

class TTSPlugin(private val context: Context) {
    private var mediaPlayer: MediaPlayer? = null
    private var pendingResult: MethodChannel.Result? = null

    fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        when (call.method) {
            "playAudio" -> {
                val path = call.argument<String>("path")
                if (path == null) {
                    result.error("INVALID_ARG", "path is required", null)
                    return
                }
                playAudio(path, result)
            }
            "stopAudio" -> {
                stopAudio()
                result.success(true)
            }
            else -> result.notImplemented()
        }
    }

    private fun playAudio(path: String, result: MethodChannel.Result) {
        try {
            stopAudio()
            val file = File(path)
            if (!file.exists()) {
                result.error("FILE_NOT_FOUND", "Audio file not found: $path", null)
                return
            }
            pendingResult = result
            mediaPlayer = MediaPlayer().apply {
                setDataSource(file.absolutePath)
                setOnPreparedListener { mp -> mp.start() }
                setOnCompletionListener { complete(null) }
                setOnErrorListener { _, what, extra ->
                    complete("MediaPlayer error: $what / $extra")
                    true
                }
                prepareAsync()
            }
        } catch (e: Exception) {
            complete(e.message)
        }
    }

    private fun complete(error: String?) {
        val result = pendingResult
        pendingResult = null
        stopAudio()
        if (result != null) {
            if (error == null) result.success(true)
            else result.error("PLAY_ERROR", error, null)
        }
    }

    private fun stopAudio() {
        val result = pendingResult
        if (result != null) {
            pendingResult = null
            result.success(true)
        }
        try {
            mediaPlayer?.apply {
                if (isPlaying) stop()
                reset()
                release()
            }
        } catch (_: Exception) {}
        mediaPlayer = null
    }
}
