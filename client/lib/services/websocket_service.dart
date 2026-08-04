import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';

class WebSocketService {
  WebSocketChannel? _channel;
  final _messageController = StreamController<Map<String, dynamic>>.broadcast();
  final _exitController = StreamController<void>.broadcast();
  bool _isConnected = false;
  String? _url;
  String? _token;
  Timer? _reconnectTimer;
  Timer? _pingTimer;

  Stream<Map<String, dynamic>> get messages => _messageController.stream;
  Stream<void> get exitApp => _exitController.stream;
  bool get isConnected => _isConnected;

  void connect(String url, {String? token}) {
    _url = url;
    _token = token;
    _reconnectTimer?.cancel();
    _pingTimer?.cancel();

    try {
      _channel?.sink.close();
    } catch (e) {}

    try {
      var uri = Uri.parse(url);
      if (token != null) {
        uri = uri.replace(queryParameters: {'token': token});
      }
      _channel = WebSocketChannel.connect(uri);

      _channel!.stream.listen(
        (data) {
          if (_messageController.isClosed) return;
          final message = json.decode(data);
          _messageController.add(message);
          if (message['type'] == 'pong') return;
          if (message['exit_app'] == true) {
            _exitController.add(null);
          }
        },
        onDone: () {
          _isConnected = false;
          _pingTimer?.cancel();
          _scheduleReconnect();
        },
        onError: (error) {
          _isConnected = false;
          _pingTimer?.cancel();
          _scheduleReconnect();
        },
      );

      _isConnected = true;
      _startPing();
    } catch (e) {
      _isConnected = false;
      _scheduleReconnect();
    }
  }

  void _startPing() {
    _pingTimer?.cancel();
    _pingTimer = Timer.periodic(Duration(seconds: 20), (_) {
      if (_isConnected) {
        send({'type': 'ping'});
      }
    });
  }

  void _scheduleReconnect() {
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(Duration(seconds: 3), () {
      if (!_isConnected && !_messageController.isClosed && _url != null) {
        connect(_url!, token: _token);
      }
    });
  }

  void send(Map<String, dynamic> message) {
    if (_isConnected && _channel != null) {
      try {
        _channel!.sink.add(json.encode(message));
      } catch (e) {
        _isConnected = false;
        _scheduleReconnect();
      }
    }
  }

  void dispose() {
    _reconnectTimer?.cancel();
    _pingTimer?.cancel();
    _messageController.close();
    _exitController.close();
    try {
      _channel?.sink.close();
    } catch (e) {}
  }
}
