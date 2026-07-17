class Message {
  final String id;
  final String role;
  final String content;
  final String type;
  final DateTime timestamp;

  Message({
    required this.id,
    required this.role,
    required this.content,
    required this.type,
    required this.timestamp,
  });

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      id: json['id'],
      role: json['role'],
      content: json['content'],
      type: json['type'],
      timestamp: DateTime.parse(json['timestamp']),
    );
  }
}

class Conversation {
  final String id;
  final String userId;
  final DateTime startedAt;
  final List<Message> messages;

  Conversation({
    required this.id,
    required this.userId,
    required this.startedAt,
    required this.messages,
  });

  factory Conversation.fromJson(Map<String, dynamic> json) {
    return Conversation(
      id: json['id'],
      userId: json['user_id'],
      startedAt: DateTime.parse(json['started_at']),
      messages: (json['messages'] as List?)
              ?.map((m) => Message.fromJson(m))
              .toList() ??
          [],
    );
  }
}
