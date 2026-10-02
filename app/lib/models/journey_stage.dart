class JourneyStage {
  const JourneyStage({
    required this.id,
    required this.title,
    required this.authority,
    required this.kind,
    required this.action,
    required this.brokerReplacement,
    required this.sourceUrl,
    this.warning,
  });

  final String id;
  final String title;
  final String authority;
  final String kind;
  final String action;
  final String brokerReplacement;
  final String sourceUrl;
  final String? warning;

  factory JourneyStage.fromJson(Map<String, dynamic> json) {
    return JourneyStage(
      id: json['id'] as String,
      title: json['title'] as String,
      authority: json['authority'] as String,
      kind: json['kind'] as String,
      action: json['action'] as String,
      brokerReplacement: json['brokerReplacement'] as String,
      sourceUrl: json['sourceUrl'] as String,
      warning: json['warning'] as String?,
    );
  }
}