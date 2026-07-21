import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../services/browser_service.dart';

class BrowserScreen extends StatefulWidget {
  final BrowserService? browserService;

  const BrowserScreen({super.key, this.browserService});

  @override
  State<BrowserScreen> createState() => _BrowserScreenState();
}

class _BrowserScreenState extends State<BrowserScreen> {
  BrowserService? _browserService;
  final _urlController = TextEditingController();
  final _searchController = TextEditingController();
  
  Uint8List? _currentScreenshot;
  String? _currentUrl;
  String? _currentTitle;
  bool _isLoading = false;
  bool _isSessionActive = false;
  List<Map<String, dynamic>> _searchResults = [];
  String? _errorMessage;

  StreamSubscription? _screenshotSubscription;
  StreamSubscription? _navigationSubscription;
  StreamSubscription? _searchSubscription;
  StreamSubscription? _sessionSubscription;
  StreamSubscription? _errorSubscription;

  @override
  void initState() {
    super.initState();
    _browserService = widget.browserService;
    _setupListeners();
  }

  @override
  void didUpdateWidget(BrowserScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.browserService != oldWidget.browserService) {
      _cancelSubscriptions();
      _browserService = widget.browserService;
      _setupListeners();
    }
  }

  void _setupListeners() {
    if (_browserService == null) return;

    _screenshotSubscription = _browserService!.screenshots.listen((screenshot) {
      setState(() {
        _currentScreenshot = screenshot;
        _isLoading = false;
      });
    });

    _navigationSubscription = _browserService!.navigationEvents.listen((event) {
      final type = event['type'];
      if (type == 'browser_navigating') {
        setState(() {
          _isLoading = true;
          _errorMessage = null;
        });
      } else if (type == 'browser_navigate_result') {
        final result = event['result'];
        if (result['status'] == 'success') {
          setState(() {
            _currentUrl = result['url'];
            _currentTitle = result['title'];
            _urlController.text = result['url'] ?? '';
          });
        } else {
          setState(() {
            _errorMessage = result['message'];
            _isLoading = false;
          });
        }
      } else if (type == 'browser_click_result' || type == 'browser_type_result') {
        final result = event['result'];
        if (result['status'] == 'error') {
          setState(() => _errorMessage = result['message']);
        }
      }
    });

    _searchSubscription = _browserService!.searchResults.listen((event) {
      final result = event['result'];
      if (result != null && result['results'] != null) {
        setState(() {
          _searchResults = List<Map<String, dynamic>>.from(result['results']);
          _isLoading = false;
        });
      }
    });

    _sessionSubscription = _browserService!.sessionEvents.listen((event) {
      final type = event['type'];
      if (type == 'browser_session_created') {
        setState(() => _isSessionActive = true);
      } else if (type == 'browser_session_destroyed') {
        setState(() {
          _isSessionActive = false;
          _currentScreenshot = null;
          _currentUrl = null;
          _currentTitle = null;
        });
      }
    });

    _errorSubscription = _browserService!.errors.listen((error) {
      setState(() {
        _errorMessage = error;
        _isLoading = false;
      });
    });
  }

  void _cancelSubscriptions() {
    _screenshotSubscription?.cancel();
    _navigationSubscription?.cancel();
    _searchSubscription?.cancel();
    _sessionSubscription?.cancel();
    _errorSubscription?.cancel();
  }

  @override
  void dispose() {
    _cancelSubscriptions();
    _urlController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  void _createSession() {
    _browserService?.createSession();
  }

  void _destroySession() {
    _browserService?.destroySession();
  }

  void _navigateToUrl() {
    final url = _urlController.text.trim();
    if (url.isNotEmpty && _browserService != null) {
      _browserService!.navigate(url);
    }
  }

  void _search() {
    final query = _searchController.text.trim();
    if (query.isNotEmpty && _browserService != null) {
      _browserService!.search(query);
    }
  }

  void _scrollUp() {
    _browserService?.scroll('up');
  }

  void _scrollDown() {
    _browserService?.scroll('down');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF0a0a1a),
      appBar: AppBar(
        backgroundColor: Color(0xFF1a1a2e),
        title: Text(
          'Browser',
          style: TextStyle(color: Colors.cyan),
        ),
        actions: [
          if (_isSessionActive)
            IconButton(
              icon: Icon(Icons.stop_circle, color: Colors.red),
              onPressed: _destroySession,
              tooltip: 'Stop Session',
            )
          else
            IconButton(
              icon: Icon(Icons.play_circle, color: Colors.green),
              onPressed: _createSession,
              tooltip: 'Start Session',
            ),
        ],
      ),
      body: Column(
        children: [
          // URL Bar
          Container(
            padding: EdgeInsets.all(8),
            color: Color(0xFF1a1a2e),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _urlController,
                    style: TextStyle(color: Colors.white),
                    decoration: InputDecoration(
                      hintText: 'Enter URL or search...',
                      hintStyle: TextStyle(color: Colors.white54),
                      prefixIcon: Icon(Icons.language, color: Colors.cyan),
                      suffixIcon: _isLoading
                          ? SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.cyan,
                              ),
                            )
                          : null,
                      filled: true,
                      fillColor: Color(0xFF2a2a4a),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                        borderSide: BorderSide.none,
                      ),
                    ),
                    onSubmitted: (_) => _navigateToUrl(),
                  ),
                ),
                SizedBox(width: 8),
                IconButton(
                  icon: Icon(Icons.search, color: Colors.cyan),
                  onPressed: _navigateToUrl,
                  tooltip: 'Navigate',
                ),
              ],
            ),
          ),

          // Search Bar
          Container(
            padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            color: Color(0xFF1a1a2e),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _searchController,
                    style: TextStyle(color: Colors.white),
                    decoration: InputDecoration(
                      hintText: 'Google search...',
                      hintStyle: TextStyle(color: Colors.white54),
                      prefixIcon: Icon(Icons.search, color: Colors.orange),
                      filled: true,
                      fillColor: Color(0xFF2a2a4a),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                        borderSide: BorderSide.none,
                      ),
                    ),
                    onSubmitted: (_) => _search(),
                  ),
                ),
                SizedBox(width: 8),
                IconButton(
                  icon: Icon(Icons.send, color: Colors.orange),
                  onPressed: _search,
                  tooltip: 'Search',
                ),
              ],
            ),
          ),

          // Navigation Controls
          Container(
            padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            color: Color(0xFF1a1a2e),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                IconButton(
                  icon: Icon(Icons.arrow_back, color: Colors.white),
                  onPressed: () => _browserService?.goBack(),
                  tooltip: 'Back',
                ),
                IconButton(
                  icon: Icon(Icons.arrow_forward, color: Colors.white),
                  onPressed: () => _browserService?.goForward(),
                  tooltip: 'Forward',
                ),
                IconButton(
                  icon: Icon(Icons.arrow_upward, color: Colors.white),
                  onPressed: _scrollUp,
                  tooltip: 'Scroll Up',
                ),
                IconButton(
                  icon: Icon(Icons.arrow_downward, color: Colors.white),
                  onPressed: _scrollDown,
                  tooltip: 'Scroll Down',
                ),
                IconButton(
                  icon: Icon(Icons.refresh, color: Colors.white),
                  onPressed: () {
                    if (_currentUrl != null) {
                      _browserService?.navigate(_currentUrl!);
                    }
                  },
                  tooltip: 'Refresh',
                ),
                IconButton(
                  icon: Icon(Icons.camera_alt, color: Colors.cyan),
                  onPressed: () => _browserService?.requestScreenshot(),
                  tooltip: 'Screenshot',
                ),
                IconButton(
                  icon: Icon(Icons.code, color: Colors.green),
                  onPressed: () => _browserService?.requestSnapshot(),
                  tooltip: 'Accessibility Tree',
                ),
              ],
            ),
          ),

          // Error Message
          if (_errorMessage != null)
            Container(
              padding: EdgeInsets.all(8),
              color: Colors.red.shade900,
              child: Row(
                children: [
                  Icon(Icons.error, color: Colors.white),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _errorMessage!,
                      style: TextStyle(color: Colors.white),
                    ),
                  ),
                  IconButton(
                    icon: Icon(Icons.close, color: Colors.white),
                    onPressed: () => setState(() => _errorMessage = null),
                  ),
                ],
              ),
            ),

          // Title Bar
          if (_currentTitle != null)
            Container(
              padding: EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              color: Color(0xFF0f0f2a),
              child: Row(
                children: [
                  Icon(Icons.web, color: Colors.cyan, size: 16),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _currentTitle!,
                      style: TextStyle(color: Colors.white70, fontSize: 12),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            ),

          // Main Content Area
          Expanded(
            child: _isSessionActive
                ? _buildBrowserView()
                : _buildSessionPlaceholder(),
          ),

          // Search Results
          if (_searchResults.isNotEmpty)
            Container(
              height: 200,
              color: Color(0xFF0f0f2a),
              child: ListView.builder(
                itemCount: _searchResults.length,
                itemBuilder: (context, index) {
                  final result = _searchResults[index];
                  return ListTile(
                    title: Text(
                      result['title'] ?? '',
                      style: TextStyle(color: Colors.cyan, fontSize: 14),
                    ),
                    subtitle: Text(
                      result['snippet'] ?? '',
                      style: TextStyle(color: Colors.white70, fontSize: 12),
                      maxLines: 2,
                    ),
                    onTap: () {
                      final url = result['link'];
                      if (url != null) {
                        _urlController.text = url;
                        _browserService?.navigate(url);
                        setState(() => _searchResults = []);
                      }
                    },
                  );
                },
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildSessionPlaceholder() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.language,
            size: 80,
            color: Colors.cyan.withOpacity(0.3),
          ),
          SizedBox(height: 16),
          Text(
            'No Browser Session',
            style: TextStyle(
              color: Colors.white54,
              fontSize: 18,
            ),
          ),
          SizedBox(height: 8),
          Text(
            'Tap the play button to start',
            style: TextStyle(
              color: Colors.white38,
              fontSize: 14,
            ),
          ),
          SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: _createSession,
            icon: Icon(Icons.play_arrow),
            label: Text('Start Browser'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.cyan,
              foregroundColor: Colors.black,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBrowserView() {
    return Stack(
      children: [
        if (_currentScreenshot != null)
          InteractiveViewer(
            minScale: 0.5,
            maxScale: 3.0,
            child: Image.memory(
              _currentScreenshot!,
              fit: BoxFit.contain,
              width: double.infinity,
              height: double.infinity,
            ),
          )
        else
          Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.web,
                  size: 60,
                  color: Colors.cyan.withOpacity(0.3),
                ),
                SizedBox(height: 16),
                Text(
                  'Enter a URL or search to begin',
                  style: TextStyle(color: Colors.white54),
                ),
              ],
            ),
          ),
        if (_isLoading)
          Center(
            child: CircularProgressIndicator(color: Colors.cyan),
          ),
      ],
    );
  }
}
