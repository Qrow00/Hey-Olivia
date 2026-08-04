import 'package:flutter/material.dart';
import '../services/personality_service.dart';
import '../services/server_config.dart';

class PersonalityScreen extends StatefulWidget {
  @override
  State<PersonalityScreen> createState() => _PersonalityScreenState();
}

class _PersonalityScreenState extends State<PersonalityScreen> {
  PersonalityService? _personalityService;
  Map _status = {};
  bool _loading = true;
  bool _error = false;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    final config = await ServerConfig.load();
    if (config == null) {
      setState(() { _loading = false; _error = true; });
      return;
    }
    _personalityService = PersonalityService(baseUrl: config.baseUrl);
    _loadStatus();
  }

  Future<void> _loadStatus() async {
    if (_personalityService == null) return;
    try {
      final status = await _personalityService!.getStatus();
      setState(() { _status = status; _loading = false; });
    } catch (_) {
      setState(() { _loading = false; _error = true; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF0a0a1a),
      appBar: AppBar(
        title: Text('Personality', style: TextStyle(color: Colors.cyan)),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: _loading
          ? Center(child: CircularProgressIndicator(color: Colors.cyan))
          : _error
          ? Center(child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.cloud_off, color: Colors.white38, size: 48),
                SizedBox(height: 16),
                Text('Cannot reach server', style: TextStyle(color: Colors.white38)),
                SizedBox(height: 8),
                TextButton(
                  onPressed: () { setState(() { _loading = true; _error = false; }); _init(); },
                  child: Text('Retry', style: TextStyle(color: Colors.cyan)),
                ),
              ],
            ))
          : SingleChildScrollView(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildHeader(),
                  SizedBox(height: 24),
                  _buildStyleSection(),
                  SizedBox(height: 24),
                  _buildStats(),
                  SizedBox(height: 24),
                  _buildFeedback(),
                ],
              ),
            ),
    );
  }

  Widget _buildHeader() {
    final style = _status['style'] ?? {};
    return Card(
      color: Colors.cyan.withValues(alpha: 0.1),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            CircleAvatar(
              radius: 32,
              backgroundColor: Colors.cyan.withValues(alpha: 0.2),
              child: Icon(Icons.psychology, color: Colors.cyan, size: 36),
            ),
            SizedBox(height: 12),
            Text(
              'J.A.R.V.I.S.',
              style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
            ),
            Text(
              'Addressed as: ${_status['preferred_name'] ?? 'Boss'}',
              style: TextStyle(color: Colors.white54, fontSize: 14),
            ),
            SizedBox(height: 8),
            Text(
              _getPersonalitySummary(style),
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white38, fontSize: 12, fontStyle: FontStyle.italic),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStyleSection() {
    final style = _status['style'] ?? {};
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Communication Style', style: TextStyle(
          color: Colors.white70, fontSize: 16, fontWeight: FontWeight.bold,
        )),
        SizedBox(height: 12),
        _styleSlider('Formality', style['formality'] ?? 0.5, (v) => _updateStyle('formality', v)),
        _styleSlider('Humor', style['humor'] ?? 0.5, (v) => _updateStyle('humor', v)),
        _styleSlider('Verbosity', style['verbosity'] ?? 0.5, (v) => _updateStyle('verbosity', v)),
        _styleSlider('Empathy', style['empathy'] ?? 0.6, (v) => _updateStyle('empathy', v)),
        _styleSlider('Directness', style['directness'] ?? 0.5, (v) => _updateStyle('directness', v)),
        _styleSlider('Enthusiasm', style['enthusiasm'] ?? 0.4, (v) => _updateStyle('enthusiasm', v)),
      ],
    );
  }

  Widget _styleSlider(String label, double value, Function(double) onChanged) {
    return Padding(
      padding: EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          SizedBox(
            width: 90,
            child: Text(label, style: TextStyle(color: Colors.white54, fontSize: 13)),
          ),
          Expanded(
            child: SliderTheme(
              data: SliderThemeData(
                activeTrackColor: Colors.cyan,
                inactiveTrackColor: Colors.white12,
                thumbColor: Colors.cyan,
                overlayColor: Colors.cyan.withValues(alpha: 0.2),
              ),
              child: Slider(
                value: value,
                min: 0,
                max: 1,
                onChanged: onChanged,
              ),
            ),
          ),
          SizedBox(
            width: 40,
            child: Text(
              '${(value * 100).toInt()}%',
              style: TextStyle(color: Colors.cyan, fontSize: 12),
              textAlign: TextAlign.right,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStats() {
    return Card(
      color: Colors.white.withValues(alpha: 0.05),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Growth Stats', style: TextStyle(
              color: Colors.white70, fontSize: 16, fontWeight: FontWeight.bold,
            )),
            SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _statItem(Icons.chat, 'Interactions', '${_status['interaction_count'] ?? 0}'),
                _statItem(Icons.lightbulb, 'Opinions', '${_status['opinion_count'] ?? 0}'),
                _statItem(Icons.auto_awesome, 'Reflections', '${_status['reflection_count'] ?? 0}'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _statItem(IconData icon, String label, String value) {
    return Column(
      children: [
        Icon(icon, color: Colors.cyan, size: 24),
        SizedBox(height: 4),
        Text(value, style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
        Text(label, style: TextStyle(color: Colors.white38, fontSize: 11)),
      ],
    );
  }

  Widget _buildFeedback() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Feedback', style: TextStyle(
          color: Colors.white70, fontSize: 16, fontWeight: FontWeight.bold,
        )),
        SizedBox(height: 12),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            _feedbackChip('Too formal', 'too_formal'),
            _feedbackChip('Too casual', 'too_casual'),
            _feedbackChip('Too long', 'too_long'),
            _feedbackChip('Too brief', 'too_brief'),
            _feedbackChip('More humor', 'more_humor'),
            _feedbackChip('Less humor', 'less_humor'),
            _feedbackChip('More empathy', 'more_empathy'),
          ],
        ),
      ],
    );
  }

  Widget _feedbackChip(String label, String type) {
    return ActionChip(
      label: Text(label, style: TextStyle(color: Colors.white70, fontSize: 12)),
      backgroundColor: Colors.white10,
      onPressed: () async {
        await _personalityService?.setFeedback(type);
        _loadStatus();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Style adjusted'), backgroundColor: Colors.cyan),
          );
        }
      },
    );
  }

  String _getPersonalitySummary(Map style) {
    final parts = <String>[];
    if ((style['formality'] ?? 0.5) > 0.7) parts.add('formal');
    if ((style['formality'] ?? 0.5) < 0.3) parts.add('casual');
    if ((style['humor'] ?? 0.5) > 0.7) parts.add('witty');
    if ((style['verbosity'] ?? 0.5) > 0.7) parts.add('detailed');
    if ((style['verbosity'] ?? 0.5) < 0.3) parts.add('concise');
    if ((style['empathy'] ?? 0.6) > 0.7) parts.add('empathetic');
    if (parts.isEmpty) parts.add('balanced');
    return parts.join(', ');
  }

  Future<void> _updateStyle(String key, double value) async {
    if (_personalityService == null) return;
    await _personalityService!.updateStyle(
      formality: key == 'formality' ? value : null,
      humor: key == 'humor' ? value : null,
      verbosity: key == 'verbosity' ? value : null,
      empathy: key == 'empathy' ? value : null,
      directness: key == 'directness' ? value : null,
      enthusiasm: key == 'enthusiasm' ? value : null,
    );
    _loadStatus();
  }
}
