import 'dart:async';
import 'dart:io';
import 'dart:typed_data';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

class AudioService {
  final AudioRecorder _recorder = AudioRecorder();
  bool _isRecording = false;
  StreamController<Uint8List>? _audioStreamController;

  bool get isRecording => _isRecording;
  Stream<Uint8List> get audioStream =>
      _audioStreamController?.stream ?? const Stream.empty();

  Future<bool> initialize() async {
    if (await _recorder.hasPermission()) {
      return true;
    }
    return false;
  }

  Future<void> startRecording({
    required Function(Uint8List) onData,
    int sampleRate = 16000,
    int bitRate = 128000,
  }) async {
    if (_isRecording) return;

    final hasPermission = await _recorder.hasPermission();
    if (!hasPermission) {
      throw Exception('Microphone permission not granted');
    }

    _audioStreamController = StreamController<Uint8List>.broadcast();

    await _recorder.start(
      RecordConfig(
        encoder: AudioEncoder.wav,
        sampleRate: sampleRate,
        bitRate: bitRate,
        numChannels: 1,
      ),
      path: '', // We'll use stream instead
    );

    _isRecording = true;

    // Start streaming
    final stream = _recorder.stream();
    stream.listen(
      (data) {
        onData(data);
        _audioStreamController?.add(data);
      },
      onError: (error) {
        print('Recording error: $error');
      },
    );
  }

  Future<String?> stopRecording() async {
    if (!_isRecording) return null;

    final path = await _recorder.stop();
    _isRecording = false;
    await _audioStreamController?.close();
    _audioStreamController = null;

    return path;
  }

  Future<void> dispose() async {
    if (_isRecording) {
      await stopRecording();
    }
    await _recorder.dispose();
    await _audioStreamController?.close();
  }
}

class AudioPlayerService {
  // For playing base64 TTS audio from backend
  static Future<void> playBase64Audio(String base64Audio) async {
    // Implementation would use audioplayers or just_audio package
    // For now, this is a placeholder
    print('Playing audio (${base64Audio.length} chars)');
  }
}