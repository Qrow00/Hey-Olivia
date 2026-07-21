import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'websocket_service.dart';

class BrowserService {
  final WebSocketService _webSocketService;

  final _sessionController = StreamController<Map<String, dynamic>>.broadcast();
  final _screenshotController = StreamController<Uint8List>.broadcast();
  final _snapshotController = StreamController<Map<String, dynamic>>.broadcast();
  final _navigationController = StreamController<Map<String, dynamic>>.broadcast();
  final _searchResultsController = StreamController<Map<String, dynamic>>.broadcast();
  final _errorController = StreamController<String>.broadcast();

  Stream<Map<String, dynamic>> get sessionEvents => _sessionController.stream;
  Stream<Uint8List> get screenshots => _screenshotController.stream;
  Stream<Map<String, dynamic>> get snapshots => _snapshotController.stream;
  Stream<Map<String, dynamic>> get navigationEvents => _navigationController.stream;
  Stream<Map<String, dynamic>> get searchResults => _searchResultsController.stream;
  Stream<String> get errors => _errorController.stream;

  String? _currentSessionId;
  String? _currentUrl;
  String? _currentTitle;

  String? get currentSessionId => _currentSessionId;
  String? get currentUrl => _currentUrl;
  String? get currentTitle => _currentTitle;

  BrowserService(this._webSocketService) {
    _webSocketService.messages.listen(_handleMessage);
  }

  void _handleMessage(Map<String, dynamic> message) {
    final type = message['type'];

    switch (type) {
      case 'browser_session_created':
        _currentSessionId = message['session_id'];
        _sessionController.add(message);
        break;
      case 'browser_session_destroyed':
        _currentSessionId = null;
        _sessionController.add(message);
        break;
      case 'browser_navigating':
        _navigationController.add(message);
        break;
      case 'browser_navigate_result':
        final result = message['result'];
        if (result['status'] == 'success') {
          _currentUrl = result['url'];
          _currentTitle = result['title'];
        }
        _navigationController.add(message);
        break;
      case 'browser_screenshot':
        final screenshotB64 = message['screenshot'];
        if (screenshotB64 != null) {
          final screenshotBytes = base64Decode(screenshotB64);
          _screenshotController.add(screenshotBytes);
        }
        if (message['url'] != null) {
          _currentUrl = message['url'];
        }
        if (message['title'] != null) {
          _currentTitle = message['title'];
        }
        break;
      case 'browser_snapshot':
        _snapshotController.add(message);
        break;
      case 'browser_click_result':
        _navigationController.add(message);
        break;
      case 'browser_type_result':
        _navigationController.add(message);
        break;
      case 'browser_scroll_result':
        _navigationController.add(message);
        break;
      case 'browser_searching':
        _navigationController.add(message);
        break;
      case 'browser_search_result':
        final result = message['result'];
        if (result != null && result['results'] != null) {
          _searchResultsController.add(message);
        }
        _navigationController.add(message);
        break;
      case 'error':
        if (message['message'] != null) {
          _errorController.add(message['message']);
        }
        break;
    }
  }

  void createSession({
    String sessionId = 'default',
    int viewportWidth = 1280,
    int viewportHeight = 720,
  }) {
    _webSocketService.send({
      'type': 'browser_create_session',
      'session_id': sessionId,
      'viewport_width': viewportWidth,
      'viewport_height': viewportHeight,
    });
  }

  void destroySession({String sessionId = 'default'}) {
    _webSocketService.send({
      'type': 'browser_destroy_session',
      'session_id': sessionId,
    });
    if (_currentSessionId == sessionId) {
      _currentSessionId = null;
    }
  }

  void navigate(String url, {String sessionId = 'default'}) {
    _webSocketService.send({
      'type': 'browser_navigate',
      'session_id': sessionId,
      'url': url,
    });
  }

  void click(String ref, {String sessionId = 'default'}) {
    _webSocketService.send({
      'type': 'browser_click',
      'session_id': sessionId,
      'ref': ref,
    });
  }

  void typeText(String ref, String text, {String sessionId = 'default'}) {
    _webSocketService.send({
      'type': 'browser_type',
      'session_id': sessionId,
      'ref': ref,
      'text': text,
    });
  }

  void requestScreenshot({String sessionId = 'default'}) {
    _webSocketService.send({
      'type': 'browser_screenshot',
      'session_id': sessionId,
    });
  }

  void requestSnapshot({String sessionId = 'default'}) {
    _webSocketService.send({
      'type': 'browser_snapshot',
      'session_id': sessionId,
    });
  }

  void scroll(String direction, {int amount = 500, String sessionId = 'default'}) {
    _webSocketService.send({
      'type': 'browser_scroll',
      'session_id': sessionId,
      'direction': direction,
      'amount': amount,
    });
  }

  void search(String query, {String sessionId = 'default'}) {
    _webSocketService.send({
      'type': 'browser_search',
      'session_id': sessionId,
      'query': query,
    });
  }

  void goBack({String sessionId = 'default'}) {
    _webSocketService.send({
      'type': 'browser_navigate',
      'session_id': sessionId,
      'url': 'javascript:history.back()',
    });
  }

  void goForward({String sessionId = 'default'}) {
    _webSocketService.send({
      'type': 'browser_navigate',
      'session_id': sessionId,
      'url': 'javascript:history.forward()',
    });
  }

  void dispose() {
    if (_currentSessionId != null) {
      destroySession(sessionId: _currentSessionId!);
    }
    _sessionController.close();
    _screenshotController.close();
    _snapshotController.close();
    _navigationController.close();
    _searchResultsController.close();
    _errorController.close();
  }
}
