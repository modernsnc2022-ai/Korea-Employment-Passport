import 'package:flutter/material.dart';
import 'journey_repository.dart';
import 'models/journey_stage.dart';
import 'stage_detail_screen.dart';

class JourneyScreen extends StatefulWidget {
  const JourneyScreen({super.key});

  @override
  State<JourneyScreen> createState() => _JourneyScreenState();
}

class _JourneyScreenState extends State<JourneyScreen> {
  late final Future<List<JourneyStage>> stages;
  int currentStage = 0;

  @override
  void initState() {
    super.initState();
    stages = JourneyRepository().loadIndonesiaManufacturing2026();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Korea Employment Passport')),
      body: FutureBuilder<List<JourneyStage>>(
        future: stages,        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return Center(child: Text('Unable to load country pack: ${snapshot.error}'));
          }
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final items = snapshot.data!;
          final progress = items.isEmpty ? 0.0 : (currentStage + 1) / items.length;
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              const Text('Indonesia → Korea',
                  style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold)),
              const Text('E-9 · Manufacturing · Zero private broker'),
              const SizedBox(height: 14),
              LinearProgressIndicator(value: progress.clamp(0, 1)),
              const SizedBox(height: 8),
              Text('Current step ${currentStage + 1} / ${items.length}'),
              const SizedBox(height: 8),
              Text(items[currentStage].title,
                  style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 20),
              ...items.asMap().entries.map((entry) {
                final index = entry.key;
                final stage = entry.value;                final isCurrent = index == currentStage;
                final isDone = index < currentStage;
                return Card(
                  child: ListTile(
                    leading: CircleAvatar(
                      child: isDone
                          ? const Icon(Icons.check, size: 18)
                          : Text((index + 1).toString()),
                    ),
                    title: Text(stage.title),
                    subtitle: Text('${stage.authority}\n${stage.action}'),
                    isThreeLine: true,
                    selected: isCurrent,
                    trailing: const Icon(Icons.chevron_right),
                    onLongPress: () => setState(() => currentStage = index),
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => StageDetailScreen(stage: stage),
                      ),
                    ),
                  ),
                );
              }),
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: () => _showBrokerGapDialog(context),
                icon: const Icon(Icons.report_problem_outlined),
                label: const Text('I still need a broker here'),
              ),
            ],
          );        },
      ),
    );
  }

  void _showBrokerGapDialog(BuildContext context) {
    final controller = TextEditingController();
    showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Broker Gap'),
        content: TextField(
          controller: controller,
          maxLines: 4,
          decoration: const InputDecoration(
            hintText: 'What task still forces you to ask an LPK, agent or broker?',
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(this.context).showSnackBar(
                const SnackBar(content: Text('Gap captured for beta review')),
              );
            },
            child: const Text('Save gap'),
          ),
        ],
      ),
    );
  }
}