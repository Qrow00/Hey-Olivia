import 'package:flutter/material.dart';
import 'dart:async';
import '../services/websocket_service.dart';
import '../services/monitoring_service.dart';

class MonitoringScreen extends StatefulWidget {
  final WebSocketService webSocketService;
  const MonitoringScreen({super.key, required this.webSocketService});

  @override
  State<MonitoringScreen> createState() => _MonitoringScreenState();
}

class _MonitoringScreenState extends State<MonitoringScreen> {
  late MonitoringService _monitoringService;
  MonitoringData? _data;
  List<AlertData> _alerts = [];
  List<ProcessData> _processes = [];
  List<ActivityEntry> _activity = [];
  int _selectedTab = 0;

  StreamSubscription? _snapshotSub;
  StreamSubscription? _alertSub;
  StreamSubscription? _processSub;
  StreamSubscription? _activitySub;

  @override
  void initState() {
    super.initState();
    _monitoringService = MonitoringService(widget.webSocketService);
    _setupListeners();
    _monitoringService.startAutoRefresh();
    _monitoringService.requestAlerts();
    _monitoringService.requestProcesses();
    _monitoringService.requestActivityLog();
  }

  void _setupListeners() {
    _snapshotSub = _monitoringService.snapshot.listen((data) {
      if (mounted) setState(() => _data = data);
    });
    _alertSub = _monitoringService.alerts.listen((alerts) {
      if (mounted) setState(() => _alerts = alerts);
    });
    _processSub = _monitoringService.processes.listen((procs) {
      if (mounted) setState(() => _processes = procs);
    });
    _activitySub = _monitoringService.activityLog.listen((log) {
      if (mounted) setState(() => _activity = log);
    });
  }

  @override
  void dispose() {
    _monitoringService.stopAutoRefresh();
    _snapshotSub?.cancel();
    _alertSub?.cancel();
    _processSub?.cancel();
    _activitySub?.cancel();
    _monitoringService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF0a0a1a),
      appBar: AppBar(
        backgroundColor: Color(0xFF1a1a2e),
        title: Row(
          children: [
            Icon(Icons.monitor_heart, color: Colors.cyan, size: 20),
            SizedBox(width: 8),
            Text('System Monitor', style: TextStyle(fontSize: 18)),
          ],
        ),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: Colors.cyan),
            onPressed: () {
              _monitoringService.requestSnapshot();
              _monitoringService.requestAlerts();
              _monitoringService.requestProcesses();
            },
          ),
        ],
      ),
      body: Column(
        children: [
          _buildTabBar(),
          Expanded(child: _buildTabContent()),
        ],
      ),
    );
  }

  Widget _buildTabBar() {
    final tabs = ['Overview', 'Processes', 'Activity', 'Alerts'];
    return Container(
      color: Color(0xFF1a1a2e),
      child: Row(
        children: List.generate(tabs.length, (i) {
          final isSelected = _selectedTab == i;
          return Expanded(
            child: GestureDetector(
              onTap: () => setState(() => _selectedTab = i),
              child: Container(
                padding: EdgeInsets.symmetric(vertical: 12),
                decoration: BoxDecoration(
                  border: Border(
                    bottom: BorderSide(
                      color: isSelected ? Colors.cyan : Colors.transparent,
                      width: 2,
                    ),
                  ),
                ),
                child: Text(
                  tabs[i],
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: isSelected ? Colors.cyan : Colors.white54,
                    fontSize: 13,
                    fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                  ),
                ),
              ),
            ),
          );
        }),
      ),
    );
  }

  Widget _buildTabContent() {
    switch (_selectedTab) {
      case 0:
        return _buildOverviewTab();
      case 1:
        return _buildProcessesTab();
      case 2:
        return _buildActivityTab();
      case 3:
        return _buildAlertsTab();
      default:
        return SizedBox.shrink();
    }
  }

  Widget _buildOverviewTab() {
    if (_data == null) {
      return Center(child: CircularProgressIndicator(color: Colors.cyan));
    }

    return SingleChildScrollView(
      padding: EdgeInsets.all(16),
      child: Column(
        children: [
          _buildSystemHealthCard(),
          SizedBox(height: 12),
          if (_data!.gpuName != null) ...[
            _buildGpuCard(),
            SizedBox(height: 12),
          ],
          _buildNetworkCard(),
          SizedBox(height: 12),
          _buildQuickStats(),
        ],
      ),
    );
  }

  Widget _buildSystemHealthCard() {
    return Card(
      color: Color(0xFF1a1a2e),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: _data!.alert ? Colors.red.withAlpha(150) : Colors.cyan.withAlpha(80),
        ),
      ),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.memory, color: Colors.cyan, size: 20),
                SizedBox(width: 8),
                Text('System Health',
                    style: TextStyle(color: Colors.cyan, fontSize: 16, fontWeight: FontWeight.bold)),
                Spacer(),
                if (_data!.alert)
                  Container(
                    padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.red.withAlpha(30),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text('ALERT', style: TextStyle(color: Colors.red, fontSize: 11, fontWeight: FontWeight.bold)),
                  ),
              ],
            ),
            SizedBox(height: 16),
            _buildMetricBar('CPU', _data!.cpuPercent, Colors.cyan,
                subtitle: _data!.cpuCount != null ? '${_data!.cpuCount} cores' : null),
            SizedBox(height: 12),
            _buildMetricBar('RAM', _data!.ramPercent, Colors.green,
                subtitle: '${_data!.ramUsedGb}GB / ${_data!.ramTotalGb}GB'),
            SizedBox(height: 12),
            _buildMetricBar('Disk', _data!.diskPercent, Colors.orange,
                subtitle: '${_data!.diskUsedGb}GB / ${_data!.diskTotalGb}GB'),
          ],
        ),
      ),
    );
  }

  Widget _buildGpuCard() {
    return Card(
      color: Color(0xFF1a1a2e),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.purple.withAlpha(80)),
      ),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.videocam, color: Colors.purple, size: 20),
                SizedBox(width: 8),
                Text('GPU', style: TextStyle(color: Colors.purple, fontSize: 16, fontWeight: FontWeight.bold)),
                Spacer(),
                Text(_data!.gpuName!, style: TextStyle(color: Colors.white54, fontSize: 12)),
              ],
            ),
            SizedBox(height: 16),
            if (_data!.gpuLoad != null)
              _buildMetricBar('Load', _data!.gpuLoad!, Colors.purple),
            SizedBox(height: 12),
            if (_data!.gpuMemoryPercent != null)
              _buildMetricBar('VRAM', _data!.gpuMemoryPercent!, Colors.purple,
                  subtitle: _data!.gpuName != null ? '' : ''),
            SizedBox(height: 12),
            if (_data!.gpuTemp != null)
              _buildMetricBar('Temp', _data!.gpuTemp!, Colors.red,
                  subtitle: '${_data!.gpuTemp!.toStringAsFixed(0)}°C'),
          ],
        ),
      ),
    );
  }

  Widget _buildNetworkCard() {
    return Card(
      color: Color(0xFF1a1a2e),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.blue.withAlpha(80)),
      ),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.network_check, color: Colors.blue, size: 20),
                SizedBox(width: 8),
                Text('Network', style: TextStyle(color: Colors.blue, fontSize: 16, fontWeight: FontWeight.bold)),
              ],
            ),
            SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildNetworkStat('Sent', _data!.netSentGb, Icons.arrow_upward),
                _buildNetworkStat('Recv', _data!.netRecvGb, Icons.arrow_downward),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNetworkStat(String label, double gb, IconData icon) {
    return Column(
      children: [
        Icon(icon, color: Colors.blue, size: 16),
        SizedBox(height: 4),
        Text('${gb.toStringAsFixed(2)} GB', style: TextStyle(color: Colors.white, fontSize: 14)),
        Text(label, style: TextStyle(color: Colors.white54, fontSize: 11)),
      ],
    );
  }

  Widget _buildQuickStats() {
    return Card(
      color: Color(0xFF1a1a2e),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.white.withAlpha(30)),
      ),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _buildStatItem(Icons.access_time, 'Uptime', '${_data!.uptimeHours.toStringAsFixed(1)}h'),
            _buildStatItem(Icons.speed, 'CPU Freq', '${_data!.cpuFreq?.toStringAsFixed(0) ?? "—"} MHz'),
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem(IconData icon, String label, String value) {
    return Column(
      children: [
        Icon(icon, color: Colors.white54, size: 18),
        SizedBox(height: 4),
        Text(value, style: TextStyle(color: Colors.white, fontSize: 14)),
        Text(label, style: TextStyle(color: Colors.white54, fontSize: 11)),
      ],
    );
  }

  Widget _buildMetricBar(String label, double value, Color color, {String? subtitle}) {
    final clamped = value.clamp(0, 100);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: TextStyle(color: Colors.white, fontSize: 13)),
            Row(
              children: [
                if (subtitle != null && subtitle.isNotEmpty)
                  Text(subtitle, style: TextStyle(color: Colors.white54, fontSize: 11)),
                if (subtitle != null && subtitle.isNotEmpty) SizedBox(width: 8),
                Text('${clamped.toStringAsFixed(1)}%',
                    style: TextStyle(color: color, fontSize: 13, fontWeight: FontWeight.bold)),
              ],
            ),
          ],
        ),
        SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: clamped / 100,
            backgroundColor: Colors.white.withAlpha(20),
            valueColor: AlwaysStoppedAnimation<Color>(
              clamped >= 90 ? Colors.red : color,
            ),
            minHeight: 6,
          ),
        ),
      ],
    );
  }

  Widget _buildProcessesTab() {
    if (_processes.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(color: Colors.cyan),
            SizedBox(height: 12),
            Text('Loading processes...', style: TextStyle(color: Colors.white54)),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: EdgeInsets.all(12),
      itemCount: _processes.length,
      itemBuilder: (context, i) {
        final p = _processes[i];
        return Card(
          color: Color(0xFF1a1a2e),
          margin: EdgeInsets.only(bottom: 6),
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor: Colors.cyan.withAlpha(30),
              child: Text('${i + 1}', style: TextStyle(color: Colors.cyan, fontSize: 12)),
            ),
            title: Text(p.name, style: TextStyle(color: Colors.white, fontSize: 13)),
            subtitle: Text('PID: ${p.pid}', style: TextStyle(color: Colors.white54, fontSize: 11)),
            trailing: Text('${p.memoryMb.toStringAsFixed(0)} MB',
                style: TextStyle(color: Colors.orange, fontSize: 12)),
          ),
        );
      },
    );
  }

  Widget _buildActivityTab() {
    if (_activity.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(color: Colors.cyan),
            SizedBox(height: 12),
            Text('Loading activity...', style: TextStyle(color: Colors.white54)),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: EdgeInsets.all(12),
      itemCount: _activity.length,
      itemBuilder: (context, i) {
        final a = _activity[_activity.length - 1 - i];
        return Card(
          color: Color(0xFF1a1a2e),
          margin: EdgeInsets.only(bottom: 6),
          child: ListTile(
            leading: Icon(
              a.category == 'window' ? Icons.window : Icons.category,
              color: Colors.cyan,
              size: 20,
            ),
            title: Text(a.detail, style: TextStyle(color: Colors.white, fontSize: 13), maxLines: 2),
            subtitle: Text(a.timestampIso.substring(11, 19),
                style: TextStyle(color: Colors.white54, fontSize: 11)),
          ),
        );
      },
    );
  }

  Widget _buildAlertsTab() {
    if (_alerts.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.check_circle, color: Colors.green, size: 48),
            SizedBox(height: 12),
            Text('No alerts', style: TextStyle(color: Colors.green, fontSize: 16)),
            Text('All systems nominal', style: TextStyle(color: Colors.white54, fontSize: 13)),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: EdgeInsets.all(12),
      itemCount: _alerts.length,
      itemBuilder: (context, i) {
        final a = _alerts[_alerts.length - 1 - i];
        final isCritical = a.severity == 'critical';
        final color = isCritical ? Colors.red : Colors.orange;
        return Card(
          color: Color(0xFF1a1a2e),
          margin: EdgeInsets.only(bottom: 6),
          shape: RoundedRectangleBorder(
            side: BorderSide(color: color.withAlpha(80)),
            borderRadius: BorderRadius.circular(8),
          ),
          child: ListTile(
            leading: Icon(
              isCritical ? Icons.error : Icons.warning,
              color: color,
              size: 24,
            ),
            title: Text(a.message, style: TextStyle(color: Colors.white, fontSize: 13)),
            subtitle: Text(a.timestamp.length > 19 ? a.timestamp.substring(0, 19) : a.timestamp,
                style: TextStyle(color: Colors.white54, fontSize: 11)),
          ),
        );
      },
    );
  }
}
