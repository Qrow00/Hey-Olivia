import 'dart:async';
import 'package:flutter/material.dart';

class NotificationItem {
  final String id;
  final String title;
  final String message;
  final String type;
  final DateTime timestamp;
  final bool isRead;

  NotificationItem({
    required this.id,
    required this.title,
    required this.message,
    required this.type,
    required this.timestamp,
    this.isRead = false,
  });
}

class NotificationService {
  final StreamController<NotificationItem> _notificationController =
      StreamController<NotificationItem>.broadcast();
  final StreamController<int> _unreadCountController =
      StreamController<int>.broadcast();

  Stream<NotificationItem> get onNotification => _notificationController.stream;
  Stream<int> get unreadCount => _unreadCountController.stream;

  final List<NotificationItem> _notifications = [];
  List<NotificationItem> get allNotifications => List.unmodifiable(_notifications);
  int get unreadCountValue => _notifications.where((n) => !n.isRead).length;

  void addNotification({
    required String title,
    required String message,
    String type = 'info',
  }) {
    final notification = NotificationItem(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      title: title,
      message: message,
      type: type,
      timestamp: DateTime.now(),
    );

    _notifications.insert(0, notification);
    if (_notifications.length > 100) {
      _notifications.removeLast();
    }

    _notificationController.add(notification);
    _unreadCountController.add(unreadCountValue);
  }

  void addHealthAlert(String metric, double value, String message) {
    addNotification(
      title: 'Health Alert: $metric',
      message: message,
      type: 'health',
    );
  }

  void addDeviceAlert(String deviceName, String message) {
    addNotification(
      title: 'Device: $deviceName',
      message: message,
      type: 'device',
    );
  }

  void addSecurityAlert(String message) {
    addNotification(
      title: 'Security Alert',
      message: message,
      type: 'security',
    );
  }

  void markAsRead(String notificationId) {
    for (var i = 0; i < _notifications.length; i++) {
      if (_notifications[i].id == notificationId) {
        _notifications[i] = NotificationItem(
          id: _notifications[i].id,
          title: _notifications[i].title,
          message: _notifications[i].message,
          type: _notifications[i].type,
          timestamp: _notifications[i].timestamp,
          isRead: true,
        );
        break;
      }
    }
    _unreadCountController.add(unreadCountValue);
  }

  void markAllAsRead() {
    for (var i = 0; i < _notifications.length; i++) {
      if (!_notifications[i].isRead) {
        _notifications[i] = NotificationItem(
          id: _notifications[i].id,
          title: _notifications[i].title,
          message: _notifications[i].message,
          type: _notifications[i].type,
          timestamp: _notifications[i].timestamp,
          isRead: true,
        );
      }
    }
    _unreadCountController.add(0);
  }

  void clearAll() {
    _notifications.clear();
    _unreadCountController.add(0);
  }

  void dispose() {
    _notificationController.close();
    _unreadCountController.close();
  }
}

class NotificationSnackbar {
  static void show(BuildContext context, String title, String message, {String type = 'info'}) {
    Color bgColor;
    IconData icon;

    switch (type) {
      case 'health':
        bgColor = Colors.red.shade900;
        icon = Icons.favorite;
        break;
      case 'security':
        bgColor = Colors.orange.shade900;
        icon = Icons.security;
        break;
      case 'device':
        bgColor = Colors.blue.shade900;
        icon = Icons.devices;
        break;
      case 'success':
        bgColor = Colors.green.shade900;
        icon = Icons.check_circle;
        break;
      case 'error':
        bgColor = Colors.red.shade900;
        icon = Icons.error;
        break;
      default:
        bgColor = Colors.grey.shade900;
        icon = Icons.info;
    }

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        backgroundColor: bgColor,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        margin: EdgeInsets.all(16),
        content: Row(
          children: [
            Icon(icon, color: Colors.white, size: 24),
            SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(title, style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14)),
                  SizedBox(height: 2),
                  Text(message, style: TextStyle(color: Colors.white70, fontSize: 12)),
                ],
              ),
            ),
          ],
        ),
        duration: Duration(seconds: 4),
      ),
    );
  }
}
