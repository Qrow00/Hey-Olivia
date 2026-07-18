import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';
import 'websocket_service.dart';

class VoiceService {
  final WebSocketService _webSocketService;
  final AudioRecorder _recorder = AudioRecorder();
  bool _isRecording = false;
  String? _recordingPath;

  final _avatarStateController = StreamController<String>.broadcast();
  final _transcriptionController = StreamController<String>.broadcast();
  final _responseController = StreamController<String>.broadcast();

  Stream<String> get avatarState => _avatarStateController.stream;
  Stream<String> get transcription => _transcriptionController.stream;
  Stream<String> get response => _responseController.stream;

  VoiceService(this._webSocketService) {
    _webSocketService.messages.listen(_handleMessage);
  }

  void _handleMessage(Map<String, dynamic> message) {
    final type = message['type'];

    switch (type) {
      case 'avatar_state':
        _avatarStateController.add(message['state']);
        break;
      case 'voice_response':
        _transcriptionController.add(message['transcription']);
        _responseController.add(message['response']);
        break;
      case 'text_response':
        _responseController.add(message['response']);
        break;
      case 'error':
        _avatarStateController.add('error');
        break;
    }
  }

  Future<bool> startListening() async {
    if (_isRecording) return false;

    if (!await _recorder.hasPermission()) {
      return false;
    }

    final dir = await getTemporaryDirectory();
    _recordingPath = '${dir.path}/recording.wav';

    await _recorder.start(
      RecordConfig(
        encoder: AudioEncoder.wav,
        numChannels: 1,
        sampleRate: 16000,
      ),
      path: _recordingPath!,
    );

    _isRecording = true;
    _avatarStateController.add('listening');
    return true;
  }

  Future<void> stopListening() async {
    if (!_isRecording) return;

    await _recorder.stop();
    _isRecording = false;

    if (_recordingPath != null) {
      final file = File(_recordingPath!);
      final audioBytes = await file.readAsBytes();
      final audioBase64 = base64Encode(audioBytes);

      _webSocketService.send({
        'type': 'voice_chunk',
        'audio': audioBase64,
      });

      await file.delete();
      _recordingPath = null;
    }
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
    _recorder.dispose();
    _avatarStateController.close();
    _transcriptionController.close();
    _responseController.close();
  }
}
