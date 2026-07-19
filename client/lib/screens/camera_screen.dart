import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../services/camera_service.dart';
import '../services/vision_service.dart';

class CameraScreen extends StatefulWidget {
  final CameraService cameraService;
  final VisionService visionService;

  const CameraScreen({
    super.key,
    required this.cameraService,
    required this.visionService,
  });

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  StreamSubscription? _frameSubscription;
  StreamSubscription? _visionSubscription;
  StreamSubscription? _observationSubscription;
  StreamSubscription? _alertSubscription;
  CameraDevice? _selectedCamera;
  Uint8List? _currentFrame;
  bool _isFullscreen = false;
  VisionResult? _lastVisionResult;
  bool _isAnalyzing = false;
  bool _isObserving = false;
  final TextEditingController _questionController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadCameras();
    _setupListeners();
  }

  void _loadCameras() async {
    await widget.cameraService.fetchCameras();
    if (mounted) setState(() {});
  }

  void _setupListeners() {
    _frameSubscription = widget.cameraService.frames.listen((frame) {
      if (mounted && frame.cameraId == _selectedCamera?.id) {
        try {
          setState(() {
            _currentFrame = base64Decode(frame.frame);
          });
        } catch (_) {}
      }
    });

    _visionSubscription = widget.visionService.results.listen((result) {
      if (mounted && result.cameraId == _selectedCamera?.id) {
        setState(() {
          _lastVisionResult = result;
          _isAnalyzing = false;
        });
      }
    });

    _observationSubscription = widget.visionService.observations.listen((obs) {
      if (mounted) {
        setState(() {
          _lastVisionResult = VisionResult(
            cameraId: '',
            cameraName: obs.camera,
            description: obs.description,
            peopleCount: obs.peopleCount,
            peopleActions: obs.peopleActions,
            motionDetected: obs.motion,
            status: 'observation',
          );
        });
      }
    });

    _alertSubscription = widget.visionService.alerts.listen((alert) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            backgroundColor: Colors.red.shade900,
            content: Row(
              children: [
                Icon(Icons.warning, color: Colors.white),
                SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(alert['camera'] ?? 'Camera', style: TextStyle(fontWeight: FontWeight.bold)),
                      Text((alert['alerts'] as List?)?.join(', ') ?? 'Alert',
                          style: TextStyle(fontSize: 12)),
                    ],
                  ),
                ),
              ],
            ),
            duration: Duration(seconds: 5),
          ),
        );
      }
    });
  }

  void _selectCamera(CameraDevice camera) {
    widget.cameraService.stopViewing();
    setState(() {
      _selectedCamera = camera;
      _currentFrame = null;
      _lastVisionResult = null;
    });
    widget.cameraService.startViewing(camera.id);
  }

  void _analyzeCurrentCamera() {
    if (_selectedCamera == null) return;
    setState(() => _isAnalyzing = true);
    widget.visionService.analyzeCamera(_selectedCamera!.id);
  }

  void _quickLook() {
    if (_selectedCamera == null) return;
    setState(() => _isAnalyzing = true);
    widget.visionService.quickLook(_selectedCamera!.id);
  }

  void _askQuestion() {
    if (_selectedCamera == null || _questionController.text.isEmpty) return;
    setState(() => _isAnalyzing = true);
    widget.visionService.askAboutCamera(_selectedCamera!.id, _questionController.text);
    _questionController.clear();
  }

  void _toggleObservation() {
    if (_isObserving) {
      widget.visionService.stopObservation();
      setState(() => _isObserving = false);
    } else {
      if (_selectedCamera == null) return;
      widget.visionService.startObservation(
        sessionId: 'camera_obs_${DateTime.now().millisecondsSinceEpoch}',
        cameraIds: [_selectedCamera!.id],
        mode: 'watch',
        interval: 15.0,
      );
      setState(() => _isObserving = true);
    }
  }

  void _scanAll() {
    setState(() => _isAnalyzing = true);
    widget.visionService.scanAllCameras();
  }

  @override
  void dispose() {
    widget.cameraService.stopViewing();
    widget.visionService.stopObservation();
    _frameSubscription?.cancel();
    _visionSubscription?.cancel();
    _observationSubscription?.cancel();
    _alertSubscription?.cancel();
    _questionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF0a0a1a),
      body: _isFullscreen ? _buildFullscreenView() : _buildMainView(),
    );
  }

  Widget _buildMainView() {
    return Column(
      children: [
        _buildHeader(),
        Expanded(
          flex: 3,
          child: _buildViewer(),
        ),
        if (_lastVisionResult != null)
          _buildVisionResult(),
        Expanded(
          flex: _lastVisionResult != null ? 1 : 2,
          child: _buildCameraList(),
        ),
      ],
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Icon(Icons.videocam, color: Colors.cyan, size: 20),
              SizedBox(width: 8),
              Text('AI Vision', style: TextStyle(color: Colors.cyan, fontSize: 16, fontWeight: FontWeight.bold)),
            ],
          ),
          Row(
            children: [
              if (_selectedCamera != null) ...[
                _buildActionButton(
                  icon: Icons.refresh,
                  onTap: _quickLook,
                  tooltip: 'Quick Look',
                  isActive: _isAnalyzing,
                ),
                _buildActionButton(
                  icon: Icons.visibility,
                  onTap: _analyzeCurrentCamera,
                  tooltip: 'Analyze Scene',
                  isActive: _isAnalyzing,
                ),
                _buildActionButton(
                  icon: _isObserving ? Icons.stop : Icons.remove_red_eye,
                  onTap: _toggleObservation,
                  tooltip: _isObserving ? 'Stop Watch' : 'Start Watch',
                  isActive: _isObserving,
                  activeColor: Colors.orange,
                ),
              ],
              _buildActionButton(
                icon: Icons.qr_code_scanner,
                onTap: _scanAll,
                tooltip: 'Scan All',
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildActionButton({
    required IconData icon,
    required VoidCallback onTap,
    String? tooltip,
    bool isActive = false,
    Color activeColor = Colors.cyan,
  }) {
    return Tooltip(
      message: tooltip ?? '',
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          margin: EdgeInsets.only(left: 8),
          padding: EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: isActive ? activeColor.withValues(alpha: 0.3) : Colors.white.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon, color: isActive ? activeColor : Colors.white70, size: 18),
        ),
      ),
    );
  }

  Widget _buildViewer() {
    return Container(
      margin: EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: Color(0xFF1a1a2e),
        borderRadius: BorderRadius.circular(16),
      ),
      child: _selectedCamera == null
          ? _buildNoCameraSelected()
          : _currentFrame == null
              ? _buildLoadingFrame()
              : _buildFrameView(),
    );
  }

  Widget _buildNoCameraSelected() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.visibility_outlined, size: 48, color: Colors.white24),
          SizedBox(height: 12),
          Text('Select a camera to view', style: TextStyle(color: Colors.white38)),
          SizedBox(height: 8),
          Text('AI can analyze and describe what it sees',
              style: TextStyle(color: Colors.white24, fontSize: 12)),
        ],
      ),
    );
  }

  Widget _buildLoadingFrame() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(color: Colors.cyan),
          SizedBox(height: 12),
          Text('Connecting...', style: TextStyle(color: Colors.white54)),
        ],
      ),
    );
  }

  Widget _buildFrameView() {
    return Stack(
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(16),
          child: Image.memory(
            _currentFrame!,
            fit: BoxFit.contain,
            gaplessPlayback: true,
          ),
        ),
        Positioned(
          top: 12,
          left: 12,
          child: Container(
            padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: Colors.red.withValues(alpha: 0.8),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(width: 6, height: 6, decoration: BoxDecoration(shape: BoxShape.circle, color: Colors.white)),
                SizedBox(width: 4),
                Text('LIVE', style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
              ],
            ),
          ),
        ),
        if (_isObserving)
          Positioned(
            top: 12,
            left: 60,
            child: Container(
              padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.orange.withValues(alpha: 0.8),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.remove_red_eye, color: Colors.white, size: 12),
                  SizedBox(width: 4),
                  Text('WATCHING', style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
                ],
              ),
            ),
          ),
        Positioned(
          top: 12,
          right: 12,
          child: Row(
            children: [
              IconButton(
                icon: Icon(Icons.question_answer, color: Colors.white),
                onPressed: _showQuestionDialog,
                tooltip: 'Ask about this view',
              ),
              IconButton(
                icon: Icon(Icons.fullscreen, color: Colors.white),
                onPressed: () => setState(() => _isFullscreen = true),
              ),
            ],
          ),
        ),
        Positioned(
          bottom: 12,
          left: 12,
          child: Text(
            _selectedCamera!.name,
            style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
          ),
        ),
      ],
    );
  }

  Widget _buildVisionResult() {
    final result = _lastVisionResult!;
    return Container(
      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Color(0xFF1a1a2e),
        borderRadius: BorderRadius.circular(12),
        border: result.alerts.isNotEmpty
            ? Border.all(color: Colors.orange.withValues(alpha: 0.5))
            : null,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              Icon(Icons.auto_awesome, color: Colors.cyan, size: 16),
              SizedBox(width: 6),
              Text('AI Analysis', style: TextStyle(color: Colors.cyan, fontSize: 12, fontWeight: FontWeight.bold)),
              Spacer(),
              if (result.peopleCount > 0)
                _buildChip('${result.peopleCount} people', Icons.person, Colors.blue),
              if (result.motionDetected)
                _buildChip('Motion', Icons.motion_photos_on, Colors.orange),
            ],
          ),
          SizedBox(height: 8),
          Text(result.description, style: TextStyle(color: Colors.white70, fontSize: 12)),
          if (result.peopleActions.isNotEmpty) ...[
            SizedBox(height: 6),
            Wrap(
              spacing: 4,
              runSpacing: 4,
              children: result.peopleActions.map((action) =>
                _buildChip(action, Icons.play_arrow, Colors.green)
              ).toList(),
            ),
          ],
          if (result.alerts.isNotEmpty) ...[
            SizedBox(height: 6),
            ...result.alerts.map((alert) => Padding(
              padding: EdgeInsets.only(top: 2),
              child: Row(
                children: [
                  Icon(Icons.warning, color: Colors.orange, size: 12),
                  SizedBox(width: 4),
                  Expanded(child: Text(alert, style: TextStyle(color: Colors.orange, fontSize: 11))),
                ],
              ),
            )),
          ],
          if (_isAnalyzing)
            Padding(
              padding: EdgeInsets.only(top: 8),
              child: Row(
                children: [
                  SizedBox(width: 12, height: 12, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.cyan)),
                  SizedBox(width: 6),
                  Text('Analyzing...', style: TextStyle(color: Colors.white38, fontSize: 11)),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildChip(String label, IconData icon, Color color) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.2),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 10),
          SizedBox(width: 2),
          Text(label, style: TextStyle(color: color, fontSize: 10)),
        ],
      ),
    );
  }

  Widget _buildCameraList() {
    final cameras = widget.cameraService.allCameras;
    return Container(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Available Cameras (${cameras.length})',
              style: TextStyle(color: Colors.white54, fontSize: 12)),
          SizedBox(height: 8),
          Expanded(
            child: cameras.isEmpty
                ? Center(
                    child: Text('No cameras configured',
                        style: TextStyle(color: Colors.white38)),
                  )
                : ListView.builder(
                    itemCount: cameras.length,
                    itemBuilder: (context, index) {
                      final camera = cameras[index];
                      final isSelected = _selectedCamera?.id == camera.id;
                      return _buildCameraCard(camera, isSelected);
                    },
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildCameraCard(CameraDevice camera, bool isSelected) {
    return GestureDetector(
      onTap: () => _selectCamera(camera),
      child: Container(
        margin: EdgeInsets.only(bottom: 8),
        padding: EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isSelected
              ? Colors.cyan.withValues(alpha: 0.2)
              : Color(0xFF1a1a2e),
          borderRadius: BorderRadius.circular(12),
          border: isSelected
              ? Border.all(color: Colors.cyan, width: 1)
              : null,
        ),
        child: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: camera.isOnline
                    ? Colors.green.withValues(alpha: 0.2)
                    : Colors.red.withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(
                Icons.videocam,
                color: camera.isOnline ? Colors.green : Colors.red,
                size: 20,
              ),
            ),
            SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(camera.name, style: TextStyle(color: Colors.white, fontSize: 14)),
                  Text(camera.location.isNotEmpty ? camera.location : camera.type.toUpperCase(),
                      style: TextStyle(color: Colors.white54, fontSize: 11)),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                _buildStatusBadge(camera.isOnline ? 'ONLINE' : 'OFFLINE', camera.isOnline),
                if (camera.viewerCount > 0) ...[
                  SizedBox(height: 4),
                  Text('${camera.viewerCount} viewers',
                      style: TextStyle(color: Colors.white38, fontSize: 10)),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusBadge(String label, bool isActive) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: isActive
            ? Colors.green.withValues(alpha: 0.2)
            : Colors.red.withValues(alpha: 0.2),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(label, style: TextStyle(
        color: isActive ? Colors.green : Colors.red,
        fontSize: 9,
        fontWeight: FontWeight.bold,
      )),
    );
  }

  Widget _buildFullscreenView() {
    if (_currentFrame == null) {
      return Center(child: CircularProgressIndicator(color: Colors.cyan));
    }

    return Stack(
      children: [
        GestureDetector(
          onTap: () => setState(() => _isFullscreen = false),
          child: Center(
            child: Image.memory(
              _currentFrame!,
              fit: BoxFit.contain,
              gaplessPlayback: true,
            ),
          ),
        ),
        Positioned(
          top: 40,
          left: 16,
          child: Container(
            padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: Colors.red.withValues(alpha: 0.8),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(width: 6, height: 6, decoration: BoxDecoration(shape: BoxShape.circle, color: Colors.white)),
                SizedBox(width: 4),
                Text('LIVE', style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
              ],
            ),
          ),
        ),
        Positioned(
          top: 40,
          right: 16,
          child: IconButton(
            icon: Icon(Icons.fullscreen_exit, color: Colors.white),
            onPressed: () => setState(() => _isFullscreen = false),
          ),
        ),
        Positioned(
          bottom: 40,
          left: 16,
          child: Text(
            _selectedCamera!.name,
            style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
          ),
        ),
        Positioned(
          bottom: 40,
          right: 16,
          child: FloatingActionButton(
            mini: true,
            backgroundColor: Colors.cyan,
            onPressed: _analyzeCurrentCamera,
            child: Icon(Icons.visibility, color: Colors.white),
          ),
        ),
      ],
    );
  }

  void _showQuestionDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: Color(0xFF1a1a2e),
        title: Row(
          children: [
            Icon(Icons.question_answer, color: Colors.cyan, size: 20),
            SizedBox(width: 8),
            Text('Ask AI', style: TextStyle(color: Colors.cyan)),
          ],
        ),
        content: TextField(
          controller: _questionController,
          style: TextStyle(color: Colors.white),
          decoration: InputDecoration(
            hintText: 'What do you want to know about this view?',
            hintStyle: TextStyle(color: Colors.white38),
            focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.cyan)),
            enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
          ),
          autofocus: true,
          onSubmitted: (value) {
            Navigator.pop(context);
            _askQuestion();
          },
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel', style: TextStyle(color: Colors.white70)),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              _askQuestion();
            },
            child: Text('Ask', style: TextStyle(color: Colors.cyan)),
          ),
        ],
      ),
    );
  }
}
