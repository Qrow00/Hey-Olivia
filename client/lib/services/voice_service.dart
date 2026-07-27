import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'dart:typed_data';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'websocket_service.dart';

enum VadState { idle, listening, speaking, processing }

enum VoicePhase { wakeWord, command }

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
  final _vadStateController = StreamController<VadState>.broadcast();
  final _ttsDoneController = StreamController<void>.broadcast();
  String _currentState = 'idle';

  VadState _vadState = VadState.idle;
  VoicePhase _voicePhase = VoicePhase.wakeWord;
  List<int> _audioBuffer = [];
  int _silenceFrames = 0;
  int _speechFrames = 0;
  bool _isProcessing = false;
  bool _alwaysListening = false;
  bool _wakeWordMode = false;
  bool _wakeWordCooldown = false;
  Process? _currentPlayer;

  static const int _sampleRate = 16000;
  static const int _bytesPerSample = 2;
  static const int _frameSize = 960;
  static const double _speechThreshold = 650.0;
  static const int _speechStartFrames = 5;
  static const int _silenceEndFrames = 25;
  static const int _minSpeechFrames = 5;
  static const int _maxBufferSeconds = 30;

  Stream<String> get avatarState => _avatarStateController.stream;
  Stream<String> get transcription => _transcriptionController.stream;
  Stream<String> get response => _responseController.stream;
  Stream<void> get exitApp => _exitController.stream;
  Stream<VadState> get vadState => _vadStateController.stream;
  Stream<void> get ttsDone => _ttsDoneController.stream;
  bool get isListening => _alwaysListening;
  bool get isRecording => _alwaysListening;
  VoicePhase get voicePhase => _voicePhase;

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
        if (message['state'] == 'idle' || message['state'] == 'error') {
          _isProcessing = false;
          _wakeWordCooldown = false;
          if (_alwaysListening) {
            _voicePhase = VoicePhase.wakeWord;
            _vadState = VadState.listening;
            _safeAdd(_vadStateController, _vadState);
          }
        }
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
        _isProcessing = false;
        break;
      case 'wake_word_detected':
        print('[Voice] Wake word detected by server, entering command phase');
        _voicePhase = VoicePhase.command;
        _isProcessing = false;
        _vadState = VadState.listening;
        _safeAdd(_vadStateController, _vadState);
        _safeAdd(_avatarStateController, 'listening');
        break;
      case 'wake_word_miss':
        _isProcessing = false;
        _vadState = VadState.listening;
        _safeAdd(_vadStateController, _vadState);
        _wakeWordCooldown = true;
        print('[Voice] Wake word miss, cooldown 2s');
        Future.delayed(Duration(seconds: 2), () {
          _wakeWordCooldown = false;
          print('[Voice] Cooldown ended, ready for next attempt');
        });
        break;
      case 'wake_word_error':
        print('[Voice] Wake word error: ${message['message']}');
        _safeAdd(_avatarStateController, 'error');
        _isProcessing = false;
        break;
    }
  }

  void _stopCurrentPlayer() {
    final player = _currentPlayer;
    if (player != null && player.pid > 0) {
      print('[Voice] Stopping previous audio');
      try {
        player.kill();
      } catch (_) {}
      _currentPlayer = null;
    }
  }

  Future<void> _playAudio(String? audioBase64) async {
    if (audioBase64 == null || audioBase64.isEmpty || _isDisposed) return;

    _stopCurrentPlayer();

    try {
      final audioBytes = base64Decode(audioBase64);
      print('[Voice] Decoded TTS: ${audioBytes.length} bytes');

      final dir = await getTemporaryDirectory();
      final file = File('${dir.path}/tts_${DateTime.now().millisecondsSinceEpoch}.mp3');
      await file.writeAsBytes(audioBytes);
      final safePath = file.path.replaceAll("'", "''");

      print('[Voice] Playing TTS via .NET MediaPlayer...');
      if (isListening && !_isDisposed) {
        await stopListening();
        print('[Voice] Paused mic during TTS playback');
      }
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
      print('[Voice] TTS playback done');
      _safeAdd(_ttsDoneController, null);
      if (!_isDisposed) {
        await Future.delayed(Duration(milliseconds: 300));
        if (!_isDisposed) {
          startListening();
          print('[Voice] Resumed mic after TTS');
        }
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
    if (_isDisposed) return false;

    if (_alwaysListening) {
      await stopListening();
      await Future.delayed(Duration(milliseconds: 300));
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
        _isProcessing = false;
      });

      _alwaysListening = true;
      _vadState = VadState.listening;
      _safeAdd(_vadStateController, _vadState);
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
    _voicePhase = VoicePhase.wakeWord;
    final started = await startListening();
    if (!started) _wakeWordMode = false;
    return started;
  }

  Future<String?> _detectDefaultMic() async {
    final mics = await listMicrophones();
    return mics.isNotEmpty ? mics.first : null;
  }

  void _processAudioStream(Stream<List<int>> audioStream) {
    List<int> remaining = [];

    audioStream.listen(
      (data) {
        final combined = [...remaining, ...data];
        remaining = [];

        int offset = 0;
        while (offset + _frameSize * _bytesPerSample <= combined.length) {
          final frame = combined.sublist(offset, offset + _frameSize * _bytesPerSample);
          offset += _frameSize * _bytesPerSample;
          _processFrame(frame);
        }

        if (offset < combined.length) {
          remaining = combined.sublist(offset);
        }
      },
      onDone: () {
        print('[Voice] Audio stream ended');
      },
      onError: (e) {
        print('[Voice] Audio stream error: $e');
      },
    );
  }

  void _processFrame(List<int> frame) {
    if (_isProcessing || _isDisposed) return;

    double rms = 0;
    for (int i = 0; i < frame.length; i += 2) {
      if (i + 1 < frame.length) {
        final sample = (frame[i] | (frame[i + 1] << 8)).toSigned(16);
        rms += sample * sample;
      }
    }
    rms = sqrt(rms / (_frameSize));

    switch (_vadState) {
      case VadState.idle:
      case VadState.listening:
        if (rms > _speechThreshold) {
          _speechFrames++;
          _silenceFrames = 0;
          if (_speechFrames >= _speechStartFrames) {
            _vadState = VadState.speaking;
            _safeAdd(_vadStateController, _vadState);
            _safeAdd(_avatarStateController, 'listening');
            _audioBuffer.addAll(frame);
            _speechFrames = 0;
            print('[Voice] Speech detected');
          }
        } else {
          _speechFrames = 0;
        }
        break;

      case VadState.speaking:
        _audioBuffer.addAll(frame);

        if (rms < _speechThreshold) {
          _silenceFrames++;
          _speechFrames = 0;
        } else {
          _silenceFrames = 0;
          _speechFrames++;
        }

        final maxFrames = _maxBufferSeconds * _sampleRate / _frameSize;
        if (_audioBuffer.length > maxFrames * _frameSize * _bytesPerSample) {
          print('[Voice] Buffer max reached, sending');
          _sendBufferedAudio();
        } else if (_silenceFrames >= _silenceEndFrames && _speechFrames < _minSpeechFrames) {
          print('[Voice] Silence detected, sending');
          _sendBufferedAudio();
        }
        break;

      case VadState.processing:
        break;
    }
  }

  void _sendBufferedAudio() {
    if (_audioBuffer.isEmpty || _isProcessing || _wakeWordCooldown) {
      _audioBuffer.clear();
      _vadState = VadState.listening;
      _safeAdd(_vadStateController, _vadState);
      return;
    }

    final totalSamples = _audioBuffer.length ~/ _bytesPerSample;
    final dataSize = _audioBuffer.length;
    final fileSize = 44 + dataSize;

    final wav = ByteData(fileSize);
    int offset = 0;

    void writeString(String s) {
      for (int i = 0; i < s.length; i++) {
        offset++;
        wav.setUint8(offset - 1, s.codeUnitAt(i));
      }
    }

    writeString('RIFF');
    wav.setUint32(offset, fileSize - 8, Endian.little); offset += 4;
    writeString('WAVE');
    writeString('fmt ');
    wav.setUint32(offset, 16, Endian.little); offset += 4;
    wav.setUint16(offset, 1, Endian.little); offset += 2;
    wav.setUint16(offset, 1, Endian.little); offset += 2;
    wav.setUint32(offset, _sampleRate, Endian.little); offset += 4;
    wav.setUint32(offset, _sampleRate * _bytesPerSample, Endian.little); offset += 4;
    wav.setUint16(offset, _bytesPerSample, Endian.little); offset += 2;
    wav.setUint16(offset, 16, Endian.little); offset += 2;
    writeString('data');
    wav.setUint32(offset, dataSize, Endian.little); offset += 4;

    for (final byte in _audioBuffer) {
      wav.setUint8(offset, byte);
      offset++;
    }

    _audioBuffer.clear();
    _silenceFrames = 0;
    _speechFrames = 0;
    _isProcessing = true;
    _vadState = VadState.processing;
    _safeAdd(_vadStateController, _vadState);

    final wavBytes = wav.buffer.asUint8List();
    print('[Voice] Sending ${wavBytes.length} bytes (${totalSamples / _sampleRate}s) phase=$_voicePhase');

    _webSocketService.send({
      'type': 'voice_chunk',
      'audio': base64Encode(wavBytes),
      'wake_word_check': _voicePhase == VoicePhase.wakeWord,
    });
  }

  Future<void> stopListening() async {
    if (!_alwaysListening || _isDisposed) return;

    _alwaysListening = false;
    _voicePhase = VoicePhase.wakeWord;
    _vadState = VadState.idle;
    _safeAdd(_vadStateController, _vadState);

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

      _audioBuffer.clear();
      _silenceFrames = 0;
      _speechFrames = 0;

      _safeAdd(_avatarStateController, 'idle');
    } catch (e) {
      print('[Voice] Stop listening error: $e');
      _safeAdd(_avatarStateController, 'idle');
    }
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
    _recordingProcess?.kill();
    _stderrSub?.cancel();
    _stdoutSub?.cancel();
    if (!_avatarStateController.isClosed) _avatarStateController.close();
    if (!_transcriptionController.isClosed) _transcriptionController.close();
    if (!_responseController.isClosed) _responseController.close();
    if (!_exitController.isClosed) _exitController.close();
    if (!_vadStateController.isClosed) _vadStateController.close();
  }
}
