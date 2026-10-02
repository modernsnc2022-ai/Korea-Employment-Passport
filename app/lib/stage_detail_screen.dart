import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'models/journey_stage.dart';

class StageDetailScreen extends StatelessWidget {
  const StageDetailScreen({super.key, required this.stage});
  final JourneyStage stage;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(stage.title)),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(stage.authority, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 16),
          Text(stage.action),
          const SizedBox(height: 20),
          Text('Broker replacement: ${stage.brokerReplacement}'),
          if (stage.warning != null) ...[
            const SizedBox(height: 20),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Text('⚠ ${stage.warning!}'),
              ),
            ),
          ],
          const SizedBox(height: 24),
          const Text('Official source', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          SelectableText(stage.sourceUrl),
          const SizedBox(height: 8),
          FilledButton.tonal(
            onPressed: () async {
              await Clipboard.setData(ClipboardData(text: stage.sourceUrl));
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Official source copied')),
                );
              }
            },
            child: const Text('Copy official source'),
          ),
        ],
      ),
    );
  }
}