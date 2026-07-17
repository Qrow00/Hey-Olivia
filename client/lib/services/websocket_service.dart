import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';

class WebSocketService {
  WebSocketChannel? _channel;
  final _messageController = StreamController<Map<String, dynamic>>.broadcast();
  bool _isConnected = false;

  Stream<Map<String, dynamic>> get messages => _messageController.stream;
  bool get isConnected => _isConnected;

  void connect(String url) {
    _channel = WebSocketChannel.connect(Uri.parse(url));

    _channel!.stream.listen(
      (data) {
        final message = json.decode(data);
        _messageController.add(message);
      },
      onDone: () {
        _isConnected = false;
        _reconnect(url);
      },
      onError: (error) {
        _isConnected = false;
      },
    );

    _isConnected = true;
  }

  void _reconnect(String url) {
    Future.delayed(Duration(seconds: 3), () {
      if (!_isConnected) {
        connect(url);
      }
    });
  }

  void send(Map<String, dynamic> message) {
    if (_isConnected) {
      _channel!.sink.add(json.encode(message));
    }
  }

  void disconnect() {
    _channel?.sink.close();
    _isConnected = false;
  }

  void dispose() {
    disconnect();
    _messageController.close();
  }
}
