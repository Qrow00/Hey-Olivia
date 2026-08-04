import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'mic_recorder.dart';
import 'websocket_service.dart';

enum VoicePhase { idle, listening, command, thinking, speaking }

class VoiceService {
  final WebSocketService _webSocketService;
  bool _isDisposed = false;
  Process? _recordingProcess;
  StreamSubscription? _stderrSub;
  StreamSubscription? _stdoutSub;

  static String _selectedMic = '';
  static String _selectedSpeaker = '';

  final _avatarStateController = StreamController<String>.broadcast();
  final _transcriptionController = StreamController<String>.broadcast();
  final _responseController = StreamController<String>.broadcast();
  final _exitController = StreamController<void>.broadcast();
  final _phaseController = StreamController<VoicePhase>.broadcast();
  final _ttsDoneController = StreamController<void>.broadcast();
  String _currentState = 'idle';

  VoicePhase _phase = VoicePhase.idle;
  bool _playbackInterrupted = false;
  final List<int> _frameBuffer = [];
  bool _alwaysListening = false;
  bool _wakeWordMode = false;
  Process? _currentPlayer;
  MicRecorder? _micRecorder;
  StreamSubscription<List<int>>? _audioStreamSub;

  static const int _sampleRate = 16000;
  static const int _frameBytes = 1280 * 2; // 80 ms of s16 mono @ 16kHz
  static const int _framesPerMessage = 4;

  Stream<String> get avatarState => _avatarStateController.stream;
  Stream<String> get transcription => _transcriptionController.stream;
  Stream<String> get response => _responseController.stream;
  Stream<void> get exitApp => _exitController.stream;
  Stream<void> get ttsDone => _ttsDoneController.stream;
  bool get isListening => _alwaysListening;
  bool get isRecording => _alwaysListening;
  VoicePhase get voicePhase => _phase;
  Stream<VoicePhase> get phase => _phaseController.stream;

  static String get _ffmpegPath {
    final ffmpegDir = '${Platform.environment['USERPROFILE']}\\ffmpeg';
    if (Directory(ffmpegDir).existsSync()) {
      return '$ffmpegDir\\ffmpeg.exe';
    }
    return 'ffmpeg';
  }

  static String get selectedMic => _selectedMic;
  static String get selectedSpeaker => _selectedSpeaker;

  VoiceService(this._webSocketService) {
    _webSocketService.messages.listen(_handleMessage, onError: (e) {
      print('[Voice] WS message error: $e');
    });
    _loadDeviceSettings();
  }

  Future<void> _loadDeviceSettings() async {
    try {
      final dir = await getApplicationDocumentsDirectory();
      final file = File('${dir.path}/jarvis_audio_devices.json');
      if (await file.exists()) {
        final data = json.decode(await file.readAsString());
        _selectedMic = data['mic'] ?? '';
        _selectedSpeaker = data['speaker'] ?? '';
      }
    } catch (_) {}
  }

  static Future<void> saveDeviceSettings(String mic, String speaker) async {
    _selectedMic = mic;
    _selectedSpeaker = speaker;
    try {
      final dir = await getApplicationDocumentsDirectory();
      final file = File('${dir.path}/jarvis_audio_devices.json');
      await file.writeAsString(json.encode({'mic': mic, 'speaker': speaker}));
    } catch (_) {}
  }

  void _safeAdd<T>(StreamController<T> controller, T value) {
    if (!_isDisposed && !controller.isClosed) {
      controller.add(value);
    }
  }

  void _handleMessage(Map<String, dynamic> message) {
    final type = message['type'];
    switch (type) {
      case 'avatar_state':
        _currentState = message['state'];
        _safeAdd(_avatarStateController, message['state']);
        break;
      case 'voice_mode_ready':
        if (message['status'] == 'error') {
          print('[Voice] Voice mode error: ${message['message']}');
          _safeAdd(_avatarStateController, 'error');
          _setPhase(VoicePhase.idle);
          stopListening();
        } else {
          print('[Voice] Voice mode ready');
          _setPhase(VoicePhase.listening);
        }
        break;
      case 'voice_phase':
        _setPhase(_parsePhase(message['phase']));
        break;
      case 'wake_word_detected':
        print('[Voice] Wake word detected');
        if (_currentPlayer != null || Platform.isAndroid) _stopCurrentPlayer();
        _setPhase(VoicePhase.command);
        _safeAdd(_avatarStateController, 'listening');
        break;
      case 'voice_response':
        _safeAdd(_transcriptionController, message['transcription'] ?? '');
        _safeAdd(_responseController, message['response'] ?? '');
        if (message['exit_app'] == true) {
          _playAudioAndExit(message['audio']);
        } else {
          _playAudio(message['audio']);
        }
        break;
      case 'text_response':
        _safeAdd(_responseController, message['response'] ?? '');
        break;
      case 'voice_error':
        print('[Voice] Voice error: ${message['message']}');
        _safeAdd(_avatarStateController, 'error');
        _setPhase(VoicePhase.listening);
        break;
      case 'error':
        _safeAdd(_avatarStateController, 'error');
        break;
    }
  }

  VoicePhase _parsePhase(dynamic value) {
    switch (value) {
      case 'listening': return VoicePhase.listening;
      case 'command': return VoicePhase.command;
      case 'thinking': return VoicePhase.thinking;
      case 'speaking': return VoicePhase.speaking;
      default: return VoicePhase.idle;
    }
  }

  void _setPhase(VoicePhase value) {
    _phase = value;
    _safeAdd(_phaseController, value);
  }

  void _stopCurrentPlayer() {
    if (_currentPlayer != null || Platform.isAndroid) {
      _playbackInterrupted = true;
    }
    if (_currentPlayer != null) {
      try { _currentPlayer!.kill(); } catch (_) {}
      _currentPlayer = null;
    }
    if (Platform.isAndroid) {
      try { _ttsChannel.invokeMethod('stopAudio'); } catch (_) {}
    }
  }

  static const _ttsChannel = MethodChannel('tts_plugin');

  Future<void> _playAudio(String? audioBase64) async {
    if (audioBase64 == null || audioBase64.isEmpty || _isDisposed) return;

    _stopCurrentPlayer();
    _playbackInterrupted = false;

    try {
      final audioBytes = base64Decode(audioBase64);
      print('[Voice] Decoded TTS: ${audioBytes.length} bytes');

      final dir = await getTemporaryDirectory();
      final file = File('${dir.path}/tts_${DateTime.now().millisecondsSinceEpoch}.mp3');
      await file.writeAsBytes(audioBytes);

      if (Platform.isWindows) {
        final safePath = file.path.replaceAll("'", "''");
        final process = await Process.start('powershell', [
          '-NoProfile', '-NonInteractive', '-Command',
          "Add-Type -AssemblyName PresentationCore; "
          "\$p = New-Object System.Windows.Media.MediaPlayer; "
          "\$p.Open([uri]::new('file:///$safePath')); "
          "\$p.Play(); "
          "Start-Sleep -Milliseconds 800; "
          "\$maxWait = 30; "
          "\$elapsed = 0; "
          "while (\$elapsed -lt \$maxWait) { "
          "  try { "
          "    if (\$p.NaturalDuration.HasTimeSpan -and \$p.Position -ge \$p.NaturalDuration.TimeSpan) { break } "
          "  } catch { break } "
          "  Start-Sleep -Milliseconds 200; "
          "  \$elapsed += 0.2; "
          "} "
          "\$p.Stop(); \$p.Close();",
        ]);
        _currentPlayer = process;
        await process.exitCode;
        _currentPlayer = null;
      } else if (Platform.isAndroid) {
        try {
          await _ttsChannel.invokeMethod('playAudio', {'path': file.path});
        } catch (e) {
          print('[Voice] Android playback error: $e');
          try { await _ttsChannel.invokeMethod('stopAudio'); } catch (_) {}
        }
      } else {
        print('[Voice] TTS playback skipped (platform: ${Platform.operatingSystem})');
      }

      if (_playbackInterrupted) {
        _playbackInterrupted = false;
        print('[Voice] Playback interrupted by barge-in, skipping tts_done');
        return;
      }

      _currentPlayer = null;
      print('[Voice] TTS playback done');
      _safeAdd(_ttsDoneController, null);
      if (!_isDisposed && !_exitPending) {
        _webSocketService.send({'type': 'tts_done'});
      }

      try {
        if (await file.exists()) await file.delete();
      } catch (_) {}
    } catch (e, stack) {
      print('[Voice] Audio playback error: $e\n$stack');
    }
  }

  bool _exitPending = false;

  void _playAudioAndExit(String? audioBase64) async {
    _exitPending = true;
    await _playAudio(audioBase64);
    _currentState = 'idle';
    _safeAdd(_avatarStateController, 'idle');
    _exitAfterIdle();
  }

  void _exitAfterIdle() {
    if (_isDisposed) return;
    StreamSubscription? sub;
    sub = _avatarStateController.stream.listen((state) {
      if (state == 'idle') {
        sub?.cancel();
        _exitPending = false;
        if (!_isDisposed) _safeAdd(_exitController, null);
      }
    });
    Timer(Duration(seconds: 30), () {
      sub?.cancel();
      _exitPending = false;
      if (!_isDisposed) _safeAdd(_exitController, null);
    });
  }

  static Future<List<String>> listMicrophones() async {
    if (!Platform.isWindows) return [];
    try {
      final result = await Process.run(
        _ffmpegPath,
        ['-list_devices', 'true', '-f', 'dshow', '-i', 'dummy'],
      );
      final output = result.stderr;
      final mics = <String>[];
      for (final line in output.split('\n')) {
        if (line.contains('(audio)') && line.contains('"')) {
          final start = line.indexOf('"') + 1;
          final end = line.lastIndexOf('"');
          if (start > 0 && end > start) {
            mics.add(line.substring(start, end));
          }
        }
      }
      return mics;
    } catch (_) {
      return [];
    }
  }

  static Future<List<String>> listSpeakers() async {
    if (!Platform.isWindows) return [];
    try {
      final result = await Process.run('powershell', [
        '-NoProfile', '-NonInteractive', '-Command',
        'Get-WmiObject Win32_SoundDevice | Select-Object -ExpandProperty Name'
      ]);
      final output = result.stdout.toString().trim();
      if (output.isEmpty) return [];
      return output.split('\n').map((s) => s.trim()).where((s) => s.isNotEmpty).toList();
    } catch (_) {
      return [];
    }
  }

  Future<bool> startListening() async {
    if (_isDisposed) return false;

    if (!Platform.isWindows && !Platform.isLinux && !Platform.isMacOS && !Platform.isAndroid) {
      print('[Voice] Voice recording not supported on this platform');
      return false;
    }

    if (_alwaysListening) {
      await stopListening();
      await Future.delayed(Duration(milliseconds: 300));
    }

    if (Platform.isAndroid) {
      return _startAndroidListening();
    }

    try {
      String micName;
      if (_selectedMic.isNotEmpty) {
        micName = _selectedMic;
      } else {
        final detected = await _detectDefaultMic();
        if (detected == null) {
          print('[Voice] No microphone found');
          return false;
        }
        micName = detected;
      }

      final args = [
        '-y', '-f', 'dshow',
        '-i', 'audio=$micName',
        '-ar', '$_sampleRate', '-ac', '1',
        '-f', 's16le',
        '-loglevel', 'error',
        'pipe:1',
      ];

      print('[Voice] Starting listening: ffmpeg $args');

      _recordingProcess = await Process.start(_ffmpegPath, args);

      _recordingProcess!.stderr.listen((data) {
        final msg = String.fromCharCodes(data).trim();
        if (msg.isNotEmpty) print('[Voice] ffmpeg stderr: $msg');
      });

      _recordingProcess!.exitCode.then((code) {
        print('[Voice] ffmpeg exited with code $code');
      });

      _alwaysListening = true;
      _safeAdd(_avatarStateController, 'listening');
      print('[Voice] Listening started');

      _processAudioStream(_recordingProcess!.stdout);

      return true;
    } catch (e) {
      print('[Voice] Start listening error: $e');
      _alwaysListening = false;
      return false;
    }
  }

  Future<bool> startWakeWordMode() async {
    if (_isDisposed) return false;
    _wakeWordMode = true;
    _setPhase(VoicePhase.idle);
    final started = await startListening();
    if (!started) {
      _wakeWordMode = false;
      return false;
    }
    _webSocketService.send({'type': 'voice_mode_start', 'sample_rate': _sampleRate});
    return true;
  }

  Future<bool> _startAndroidListening() async {
    try {
      _micRecorder ??= MicRecorder();
      _processAudioStream(_micRecorder!.pcm);
      final started = await _micRecorder!.start();
      if (!started) {
        print('[Voice] Android mic start failed');
        _audioStreamSub?.cancel();
        _audioStreamSub = null;
        _safeAdd(_avatarStateController, 'error');
        return false;
      }
      _alwaysListening = true;
      _safeAdd(_avatarStateController, 'listening');
      print('[Voice] Android listening started');
      return true;
    } catch (e) {
      print('[Voice] Android start listening error: $e');
      _alwaysListening = false;
      _safeAdd(_avatarStateController, 'error');
      return false;
    }
  }

  Future<String?> _detectDefaultMic() async {
    final mics = await listMicrophones();
    return mics.isNotEmpty ? mics.first : null;
  }

  void _processAudioStream(Stream<List<int>> audioStream) {
    _audioStreamSub?.cancel();
    _audioStreamSub = audioStream.listen(
      (data) {
        _frameBuffer.addAll(data);
        while (_frameBuffer.length >= _framesPerMessage * _frameBytes) {
          final chunk = _frameBuffer.sublist(0, _framesPerMessage * _frameBytes);
          _frameBuffer.removeRange(0, _framesPerMessage * _frameBytes);
          _sendAudioFrame(chunk);
        }
      },
      onDone: () => print('[Voice] Audio stream ended'),
      onError: (e) => print('[Voice] Audio stream error: $e'),
    );
  }

  void _sendAudioFrame(List<int> pcm) {
    _webSocketService.send({
      'type': 'audio_frame',
      'audio': base64Encode(Uint8List.fromList(pcm)),
    });
  }

  Future<void> stopListening() async {
    if (!_alwaysListening && !_wakeWordMode) return;
    _alwaysListening = false;
    _wakeWordMode = false;
    _setPhase(VoicePhase.idle);
    try { _webSocketService.send({'type': 'voice_mode_stop'}); } catch (_) {}
    try { await _audioStreamSub?.cancel(); } catch (_) {}
    _audioStreamSub = null;
    _frameBuffer.clear();
    if (Platform.isAndroid) {
      await _micRecorder?.stop();
    } else if (_recordingProcess != null) {
      try {
        _recordingProcess!.stdin.write('q');
        await _recordingProcess!.stdin.flush();
      } catch (_) {}
      await _stderrSub?.cancel();
      await _stdoutSub?.cancel();
      final exitCode = await _recordingProcess!.exitCode.timeout(
        Duration(seconds: 3),
        onTimeout: () {
          _recordingProcess?.kill();
          return -1;
        },
      );
      print('[Voice] ffmpeg exit: $exitCode');
      _recordingProcess = null;
    }
    _safeAdd(_avatarStateController, 'idle');
  }

  void sendTextMessage(String text, {String? systemPrompt}) {
    _webSocketService.send({
      'type': 'text_message',
      'text': text,
      'system_prompt': systemPrompt ?? 'You are J.A.R.V.I.S., a helpful AI assistant.',
    });
  }

  void dispose() {
    _isDisposed = true;
    _alwaysListening = false;
    _audioStreamSub?.cancel();
    _audioStreamSub = null;
    _micRecorder?.stop();
    _recordingProcess?.kill();
    _stderrSub?.cancel();
    _stdoutSub?.cancel();
    if (!_avatarStateController.isClosed) _avatarStateController.close();
    if (!_transcriptionController.isClosed) _transcriptionController.close();
    if (!_responseController.isClosed) _responseController.close();
    if (!_exitController.isClosed) _exitController.close();
    if (!_phaseController.isClosed) _phaseController.close();
  }
}
