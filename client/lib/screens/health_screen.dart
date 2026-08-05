import 'dart:async';
import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../models/wearable.dart';
import '../services/wearable_service.dart';
import '../utils/responsive.dart';
import '../utils/theme.dart';

const _bg = AppTheme.bg;
const _panel = AppTheme.panel;
const _hud = AppTheme.hud;
const _hudDim = AppTheme.hudDim;
const _text = AppTheme.text;
const _textDim = AppTheme.textDim;
const _danger = AppTheme.accentAmber;
const _success = AppTheme.accentGreen;

class HealthScreen extends StatefulWidget {
  final WearableService wearableService;

  const HealthScreen({super.key, required this.wearableService});

  @override
  State<HealthScreen> createState() => _HealthScreenState();
}

class _HealthScreenState extends State<HealthScreen> {
  StreamSubscription? _healthSubscription;
  WearableDevice? _selectedDevice;
  final Map<String, List<double>> _history = {};
  bool _historyLoaded = false;

  @override
  void initState() {
    super.initState();
    _loadDevices();
  }

  void _loadDevices() async {
    await widget.wearableService.fetchDevices();
    if (widget.wearableService.allDevices.isNotEmpty) {
      setState(() {
        _selectedDevice = widget.wearableService.allDevices.first;
      });
      await _loadHistory();
    }
    _healthSubscription = widget.wearableService.healthUpdates.listen((_) {
      if (mounted) setState(() {});
    });
  }

  Future<void> _loadHistory() async {
    if (_selectedDevice == null) return;
    _historyLoaded = true;
    final metrics = ['heart_rate', 'spo2', 'steps', 'sleep', 'calories', 'stress'];
    for (final m in metrics) {
      final data = await widget.wearableService.getHealthHistory(
        _selectedDevice!.id,
        metric: m,
        limit: 20,
      );
      if (data.isNotEmpty) {
        _history[m] = data.map((d) => (d['value'] as num).toDouble()).toList();
      }
    }
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    _healthSubscription?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bg,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text('HEALTH MONITOR', style: TextStyle(color: _hud, fontSize: 14, letterSpacing: 2)),
        actions: [
          IconButton(icon: Icon(Icons.refresh, color: _hud, size: 20), onPressed: _loadDevices),
        ],
      ),
      body: _selectedDevice == null ? _buildNoDevice() : _buildDashboard(),
    );
  }

  Widget _buildNoDevice() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 80, height: 80,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: _hud.withValues(alpha: 0.08),
              border: Border.all(color: _hud.withValues(alpha: 0.2), width: 1),
            ),
            child: Icon(Icons.watch_outlined, size: 36, color: _hudDim),
          ),
          SizedBox(height: 20),
          Text('NO DEVICE CONNECTED', style: TextStyle(color: _textDim, fontSize: 13, letterSpacing: 1.5)),
          SizedBox(height: 8),
          Text('Pair a wearable to monitor your vitals', style: TextStyle(color: _textDim, fontSize: 11)),
        ],
      ),
    );
  }

  Widget _buildDashboard() {
    final health = _selectedDevice!.healthSummary;
    return RefreshIndicator(
      onRefresh: () async => _loadDevices(),
      color: _hud,
      backgroundColor: _panel,
      child: SingleChildScrollView(
        physics: AlwaysScrollableScrollPhysics(),
        padding: Display.padding(context),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildDeviceHeader(),
            SizedBox(height: Display.cardGap(context)),
            LayoutBuilder(
              builder: (context, constraints) {
                final cols = Display.gridColumns(context);
                final gap = Display.cardGap(context).toDouble();
                final childW = (constraints.maxWidth - (cols - 1) * gap) / cols;
                return Wrap(
                  spacing: gap,
                  runSpacing: gap,
                  children: [
                    SizedBox(width: childW, child: _buildVitalCard(Icons.favorite, 'HEART RATE', health?.heartRate?.current?.toInt(), 'bpm', Colors.red, health?.heartRate?.avg?.toInt())),
                    SizedBox(width: childW, child: _buildVitalCard(Icons.air, 'BLOOD OXYGEN', health?.spo2?.current?.toInt(), '%', Colors.blue, health?.spo2?.avg?.toInt())),
                    SizedBox(width: childW, child: _buildVitalCard(Icons.directions_walk, 'STEPS', health?.steps?.todayTotal?.toInt(), 'today', _success, null)),
                    SizedBox(width: childW, child: _buildVitalCard(Icons.bedtime_outlined, 'SLEEP', health?.sleep?.current?.toInt(), 'hrs', Colors.purple, null)),
                    SizedBox(width: childW, child: _buildVitalCard(Icons.local_fire_department, 'CALORIES', health?.calories?.current?.toInt(), 'kcal', _danger, null)),
                    SizedBox(width: childW, child: _buildVitalCard(Icons.psychology, 'STRESS', health?.stress?.current?.toInt(), '', Colors.teal, null)),
                  ],
                );
              },
            ),
            SizedBox(height: Display.cardGap(context)),
            _buildAlertsSection(),
          ],
        ),
      ),
    );
  }

  Widget _buildDeviceHeader() {
    return Container(
      padding: EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: _panel,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: _hud.withValues(alpha: 0.1), width: 0.5),
      ),
      child: Row(
        children: [
          Container(
            width: 40, height: 40,
            decoration: BoxDecoration(
              color: _hud.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(Icons.watch, color: _hud, size: 22),
          ),
          SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_selectedDevice!.name, style: TextStyle(color: _text, fontSize: 14, fontWeight: FontWeight.w600)),
                Text(_selectedDevice!.type.toUpperCase(), style: TextStyle(color: _textDim, fontSize: 10, letterSpacing: 1)),
              ],
            ),
          ),
          _buildChip(_selectedDevice!.isOnline ? 'ONLINE' : 'OFFLINE', _selectedDevice!.isOnline ? _success : Colors.red),
          SizedBox(width: 8),
          _buildBattery(_selectedDevice!.battery),
        ],
      ),
    );
  }

  Widget _buildChip(String label, Color color) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        border: Border.all(color: color.withValues(alpha: 0.4), width: 0.5),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(label, style: TextStyle(color: color, fontSize: 9, letterSpacing: 1)),
    );
  }

  Widget _buildBattery(int level) {
    Color c = level > 50 ? _success : (level > 20 ? _danger : Colors.red);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(Icons.battery_std, color: c, size: 16),
        Text('$level%', style: TextStyle(color: c, fontSize: 9)),
      ],
    );
  }

  Widget _buildSparkline(String metricKey, Color color) {
    final data = _history[metricKey];
    if (data == null || data.length < 2) return SizedBox.shrink();
    final min = data.reduce((a, b) => a < b ? a : b);
    final max = data.reduce((a, b) => a > b ? a : b);
    final range = (max - min).clamp(1.0, double.infinity);
    return SizedBox(
      width: 60, height: 28,
      child: LineChart(
        LineChartData(
          gridData: FlGridData(show: false),
          titlesData: FlTitlesData(show: false),
          borderData: FlBorderData(show: false),
          lineBarsData: [
            LineChartBarData(
              spots: List.generate(data.length, (i) => FlSpot(i.toDouble(), data[i])),
              isCurved: true,
              preventCurveOverShooting: true,
              color: color,
              barWidth: 1.5,
              dotData: FlDotData(show: false),
              belowBarData: BarAreaData(show: true, color: color.withValues(alpha: 0.08)),
            ),
          ],
          minY: min - range * 0.1,
          maxY: max + range * 0.1,
        ),
      ),
    );
  }

  Widget _buildVitalCard(IconData icon, String label, int? value, String unit, Color color, int? avg) {
    final metricKey = _metricKey(label);
    return Container(
      padding: EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: _panel,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.08), width: 0.5),
      ),
      child: Row(
        children: [
          Container(
            width: 40, height: 40,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: color, size: 20),
          ),
          SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: TextStyle(color: _textDim, fontSize: 10, letterSpacing: 1.2)),
                SizedBox(height: 2),
                value != null
                    ? Text('$value', style: TextStyle(color: _text, fontSize: 26, fontWeight: FontWeight.w300))
                    : Text('--', style: TextStyle(color: _textDim, fontSize: 26)),
              ],
            ),
          ),
          _buildSparkline(metricKey, color),
          SizedBox(width: 8),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              if (unit.isNotEmpty)
                Text(unit, style: TextStyle(color: _textDim, fontSize: 11)),
              if (avg != null) ...[
                SizedBox(height: 4),
                Text('AVG $avg', style: TextStyle(color: _textDim, fontSize: 9)),
              ],
            ],
          ),
        ],
      ),
    );
  }

  String _metricKey(String label) {
    final map = {
      'HEART RATE': 'heart_rate',
      'BLOOD OXYGEN': 'spo2',
      'STEPS': 'steps',
      'SLEEP': 'sleep',
      'CALORIES': 'calories',
      'STRESS': 'stress',
    };
    return map[label] ?? label.toLowerCase();
  }

  Widget _buildAlertsSection() {
    return Container(
      padding: EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: _panel,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: _danger.withValues(alpha: 0.08), width: 0.5),
      ),
      child: Row(
        children: [
          Icon(Icons.warning_amber_rounded, color: _danger, size: 18),
          SizedBox(width: 10),
          Text('ALL VITALS NOMINAL', style: TextStyle(color: _textDim, fontSize: 11, letterSpacing: 1)),
        ],
      ),
    );
  }
}
