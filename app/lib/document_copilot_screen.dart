import 'package:flutter/material.dart';

class DocumentCopilotScreen extends StatelessWidget {
  const DocumentCopilotScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final items = const [
      ['KTP', 'Required', 'Check name and date of birth'],
      ['Passport', 'If available / current notice', 'Check identity match'],
      ['Photo', 'Required', 'Check background, framing and file spec'],
      ['Diploma', 'Required', 'Check minimum education and readable scan'],
      ['Bank account', 'Required by current registration flow', 'Must belong to applicant'],
    ];
    return Scaffold(
      appBar: AppBar(title: const Text('Document Copilot')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('Pre-check before official submission',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          ...items.map((item) => Card(
                child: ListTile(
                  title: Text(item[0]),
                  subtitle: Text('${item[1]}\n${item[2]}'),
                  isThreeLine: true,
                  trailing: const Icon(Icons.chevron_right),
                ),
              )),
        ],
      ),
    );
  }
}