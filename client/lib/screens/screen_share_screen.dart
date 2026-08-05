import 'dart:async';
import 'dart:typed_data';
import 'dart:convert';
import 'package:flutter/material.dart';
import '../services/screen_share_service.dart';
import '../utils/theme.dart';

const _bg = AppTheme.bg;
const _panel = AppTheme.panel;

class ScreenShareScreen extends StatefulWidget {
  final ScreenShareService? screenShareService;

  const ScreenShareScreen({super.key, this.screenShareService});

  @override
  State<ScreenShareScreen> createState() => _ScreenShareScreenState();
}

class _ScreenShareScreenState extends State<ScreenShareScreen> {
  ScreenShareService? _screenShareService;
  Uint8List? _currentFrame;
  int _viewerCount = 0;
  String _status = 'idle';
  String? _analysisResult;
  bool _isAnalyzing = false;
  bool _isCapturing = false;

  StreamSubscription? _frameSubscription;
  StreamSubscription? _viewerSubscription;
  StreamSubscription? _analysisSubscription;
  StreamSubscription? _sessionSubscription;

  @override
  void initState() {
    super.initState();
    _screenShareService = widget.screenShareService;
    _setupListeners();
    _checkCaptureStatus();
  }

  @override
  void didUpdateWidget(ScreenShareScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.screenShareService != oldWidget.screenShareService) {
      _cancelSubscriptions();
      _screenShareService = widget.screenShareService;
      _setupListeners();
    }
  }

  void _setupListeners() {
    if (_screenShareService == null) return;

    _frameSubscription = _screenShareService!.frames.listen((frame) {
      setState(() => _currentFrame = frame);
    });

    _viewerSubscription = _screenShareService!.viewerCount.listen((count) {
      setState(() => _viewerCount = count);
    });

    _analysisSubscription = _screenShareService!.analysis.listen((result) {
      setState(() {
        _analysisResult = result['description'];
        _isAnalyzing = false;
      });
    });

    _sessionSubscription = _screenShareService!.sessionEvents.listen((event) {
      final type = event['type'];
      if (type == 'screen_started') {
        setState(() {
          _status = 'streaming';
          _isCapturing = true;
        });
      } else if (type == 'screen_stopped') {
        setState(() {
          _status = 'idle';
          _currentFrame = null;
          _isCapturing = false;
        });
      } else if (type == 'screen_viewing') {
        setState(() => _status = 'viewing');
      }
    });
  }

  void _cancelSubscriptions() {
    _frameSubscription?.cancel();
    _viewerSubscription?.cancel();
    _analysisSubscription?.cancel();
    _sessionSubscription?.cancel();
  }

  Future<void> _checkCaptureStatus() async {
    if (_screenShareService != null) {
      final capturing = await _screenShareService!.isCapturing();
      setState(() => _isCapturing = capturing);
    }
  }

  @override
  void dispose() {
    _cancelSubscriptions();
    super.dispose();
  }

  void _toggleStreaming() {
    if (_screenShareService == null) return;

    if (_isCapturing) {
      _screenShareService!.stopStreaming();
    } else {
      _showCaptureSettingsDialog();
    }
  }

  void _showCaptureSettingsDialog() {
    int fps = 5;
    int quality = 80;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          backgroundColor: _panel,
          title: Text('Screen Capture Settings', style: TextStyle(color: Colors.cyan)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('FPS', style: TextStyle(color: Colors.white70)),
                  Slider(
                    value: fps.toDouble(),
                    min: 1,
                    max: 15,
                    divisions: 14,
                    activeColor: Colors.cyan,
                    onChanged: (v) => setDialogState(() => fps = v.round()),
                  ),
                  Text('$fps', style: TextStyle(color: Colors.cyan)),
                ],
              ),
              SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('Quality', style: TextStyle(color: Colors.white70)),
                  Slider(
                    value: quality.toDouble(),
                    min: 30,
                    max: 100,
                    divisions: 7,
                    activeColor: Colors.cyan,
                    onChanged: (v) => setDialogState(() => quality = v.round()),
                  ),
                  Text('$quality%', style: TextStyle(color: Colors.cyan)),
                ],
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text('Cancel', style: TextStyle(color: Colors.white70)),
            ),
            TextButton(
              onPressed: () {
                Navigator.pop(context);
                _startCaptureWithSettings(fps, quality);
              },
              child: Text('Start', style: TextStyle(color: Colors.cyan)),
            ),
          ],
        ),
      ),
    );
  }

  void _startCaptureWithSettings(int fps, int quality) {
    _screenShareService!.startStreaming(
      deviceId: 'self',
      fps: fps,
      quality: quality,
    );
  }

  void _requestAnalysis() {
    if (_screenShareService == null || _currentFrame == null) return;

    setState(() {
      _isAnalyzing = true;
      _analysisResult = null;
    });

    _screenShareService!.requestAnalysis(
      _screenShareService!.currentSessionId ?? '',
      frame: base64Encode(_currentFrame!),
      prompt: 'Describe what is on this screen in detail',
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bg,
      appBar: AppBar(
        title: Text('Screen Share'),
        backgroundColor: _panel,
        actions: [
          if (_viewerCount > 0)
            Padding(
              padding: EdgeInsets.only(right: 16),
              child: Center(
                child: Row(
                  children: [
                    Icon(Icons.visibility, color: Colors.cyan, size: 18),
                    SizedBox(width: 4),
                    Text(
                      '$_viewerCount',
                      style: TextStyle(color: Colors.cyan),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
      body: Column(
        children: [
          _buildControlBar(),
          Expanded(child: _buildViewer()),
          if (_analysisResult != null) _buildAnalysisPanel(),
        ],
      ),
    );
  }

  Widget _buildControlBar() {
    return Container(
      padding: EdgeInsets.all(16),
      color: _panel,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _buildControlButton(
            icon: _isCapturing ? Icons.stop : Icons.play_arrow,
            label: _isCapturing ? 'Stop' : 'Start',
            color: _isCapturing ? Colors.red : Colors.green,
            onTap: _toggleStreaming,
          ),
          _buildControlButton(
            icon: Icons.analytics,
            label: 'Analyze',
            color: Colors.orange,
            onTap: _currentFrame != null ? _requestAnalysis : null,
            enabled: _currentFrame != null && !_isAnalyzing,
          ),
          _buildControlButton(
            icon: Icons.fullscreen,
            label: 'Fullscreen',
            color: Colors.cyan,
            onTap: _currentFrame != null ? _enterFullscreen : null,
            enabled: _currentFrame != null,
          ),
        ],
      ),
    );
  }

  Widget _buildControlButton({
    required IconData icon,
    required String label,
    required Color color,
    VoidCallback? onTap,
    bool enabled = true,
  }) {
    return GestureDetector(
      onTap: enabled ? onTap : null,
      child: Opacity(
        opacity: enabled ? 1.0 : 0.4,
        child: Column(
          children: [
            Container(
              padding: EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: color.withValues(alpha: 0.5)),
              ),
              child: Icon(icon, color: color, size: 28),
            ),
            SizedBox(height: 6),
            Text(label, style: TextStyle(color: Colors.white70, fontSize: 12)),
          ],
        ),
      ),
    );
  }

  Widget _buildViewer() {
    if (_currentFrame == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.screen_share, color: Colors.white24, size: 80),
            SizedBox(height: 16),
            Text(
              _isCapturing ? 'Waiting for frames...' : 'No active screen share',
              style: TextStyle(color: Colors.white54, fontSize: 16),
            ),
            SizedBox(height: 8),
            Text(
              'Tap Start to begin capturing your screen',
              style: TextStyle(color: Colors.white38, fontSize: 14),
            ),
          ],
        ),
      );
    }

    return Stack(
      fit: StackFit.expand,
      children: [
        Image.memory(
          _currentFrame!,
          fit: BoxFit.contain,
          gaplessPlayback: true,
        ),
        if (_isAnalyzing)
          Positioned(
            top: 16,
            right: 16,
            child: Container(
              padding: EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.orange.withValues(alpha: 0.9),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Colors.white,
                    ),
                  ),
                  SizedBox(width: 8),
                  Text('Analyzing...', style: TextStyle(color: Colors.white)),
                ],
              ),
            ),
          ),
        Positioned(
          top: 16,
          left: 16,
          child: Container(
            padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: Colors.black.withValues(alpha: 0.7),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.red,
                  ),
                ),
                SizedBox(width: 6),
                Text(
                  'LIVE',
                  style: TextStyle(
                    color: Colors.red,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildAnalysisPanel() {
    return Container(
      padding: EdgeInsets.all(16),
      color: _panel,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'SCREEN ANALYSIS',
                style: TextStyle(
                  color: Colors.cyan,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
              ),
              IconButton(
                icon: Icon(Icons.close, color: Colors.white54, size: 18),
                onPressed: () => setState(() => _analysisResult = null),
              ),
            ],
          ),
          SizedBox(height: 8),
          Text(
            _analysisResult!,
            style: TextStyle(color: Colors.white70, fontSize: 14),
          ),
        ],
      ),
    );
  }

  void _enterFullscreen() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => _FullscreenViewer(frame: _currentFrame!),
      ),
    );
  }
}

class _FullscreenViewer extends StatelessWidget {
  final Uint8List frame;

  const _FullscreenViewer({required this.frame});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: GestureDetector(
        onTap: () => Navigator.pop(context),
        child: Center(
          child: Image.memory(
            frame,
            fit: BoxFit.contain,
            gaplessPlayback: true,
          ),
        ),
      ),
    );
  }
}
