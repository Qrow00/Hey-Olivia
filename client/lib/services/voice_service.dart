import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'websocket_service.dart';

class VoiceService {
  final WebSocketService _webSocketService;
  bool _isRecording = false;
  bool _isDisposed = false;
  Process? _recordingProcess;
  String? _recordingPath;
  StreamSubscription? _stderrSub;
  StreamSubscription? _stdoutSub;

  static String _selectedMic = '';
  static String _selectedSpeaker = '';

  final _avatarStateController = StreamController<String>.broadcast();
  final _transcriptionController = StreamController<String>.broadcast();
  final _responseController = StreamController<String>.broadcast();
  final _exitController = StreamController<void>.broadcast();
  String _currentState = 'idle';

  Stream<String> get avatarState => _avatarStateController.stream;
  Stream<String> get transcription => _transcriptionController.stream;
  Stream<String> get response => _responseController.stream;
  Stream<void> get exitApp => _exitController.stream;

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
      case 'error':
        _safeAdd(_avatarStateController, 'error');
        break;
    }
  }

  Future<void> _playAudio(String? audioBase64) async {
    if (audioBase64 == null || audioBase64.isEmpty || _isDisposed) return;

    try {
      final audioBytes = base64Decode(audioBase64);
      print('[Voice] Decoded TTS: ${audioBytes.length} bytes');

      final dir = await getTemporaryDirectory();
      final file = File('${dir.path}/tts_${DateTime.now().millisecondsSinceEpoch}.mp3');
      await file.writeAsBytes(audioBytes);
      final safePath = file.path.replaceAll("'", "''");

      print('[Voice] Playing TTS via .NET MediaPlayer...');
      final result = await Process.run('powershell', [
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
      print('[Voice] TTS playback done (exit: ${result.exitCode})');

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
    if (_isRecording || _isDisposed) return false;

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

      final dir = await getTemporaryDirectory();
      _recordingPath = '${dir.path}/recording.wav';

      final args = [
        '-y', '-f', 'dshow',
        '-i', 'audio=$micName',
        '-ar', '16000', '-ac', '1',
        '-loglevel', 'error',
        _recordingPath!,
      ];

      print('[Voice] ffmpeg: $args');

      _recordingProcess = await Process.start(_ffmpegPath, args);

      _stdoutSub = _recordingProcess!.stdout.listen(
        (_) {},
        onError: (_) {},
      );
      _stderrSub = _recordingProcess!.stderr.listen(
        (_) {},
        onError: (_) {},
      );

      _isRecording = true;
      _safeAdd(_avatarStateController, 'listening');
      print('[Voice] Recording started');
      return true;
    } catch (e) {
      print('[Voice] Start recording error: $e');
      _isRecording = false;
      _recordingPath = null;
      return false;
    }
  }

  Future<String?> _detectDefaultMic() async {
    final mics = await listMicrophones();
    return mics.isNotEmpty ? mics.first : null;
  }

  Future<void> stopListening() async {
    if (!_isRecording || _isDisposed) return;

    _isRecording = false;
    _safeAdd(_avatarStateController, 'thinking');

    try {
      if (_recordingProcess != null) {
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

      await Future.delayed(Duration(milliseconds: 300));

      if (_recordingPath == null) {
        _safeAdd(_avatarStateController, 'idle');
        return;
      }

      final file = File(_recordingPath!);
      if (!await file.exists()) {
        print('[Voice] Recording file missing');
        _safeAdd(_avatarStateController, 'idle');
        return;
      }

      final audioBytes = await file.readAsBytes();
      print('[Voice] Recording: ${audioBytes.length} bytes');

      if (audioBytes.length < 1000) {
        print('[Voice] Recording too short');
        _safeAdd(_avatarStateController, 'idle');
        try { await file.delete(); } catch (_) {}
        return;
      }

      _webSocketService.send({
        'type': 'voice_chunk',
        'audio': base64Encode(audioBytes),
      });
      print('[Voice] Sent voice_chunk');

      try { await file.delete(); } catch (_) {}
    } catch (e) {
      print('[Voice] Stop recording error: $e');
      _safeAdd(_avatarStateController, 'idle');
    }

    _recordingPath = null;
  }

  void sendTextMessage(String text, {String? systemPrompt}) {
    _webSocketService.send({
      'type': 'text_message',
      'text': text,
      'system_prompt': systemPrompt ?? 'You are J.A.R.V.I.S., a helpful AI assistant.',
    });
  }

  bool get isRecording => _isRecording;

  void dispose() {
    _isDisposed = true;
    _recordingProcess?.kill();
    _stderrSub?.cancel();
    _stdoutSub?.cancel();
    if (!_avatarStateController.isClosed) _avatarStateController.close();
    if (!_transcriptionController.isClosed) _transcriptionController.close();
    if (!_responseController.isClosed) _responseController.close();
    if (!_exitController.isClosed) _exitController.close();
  }
}
