import 'package:flutter/material.dart';

class CostLedgerScreen extends StatelessWidget {
  const CostLedgerScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final costs = const [
      ['EPS-TOPIK fee', 'Verify current official notice before payment', 'Official'],
      ['Psychology test', 'Use current KP2MI/HIMPSI notice', 'Official/conditional'],
      ['Medical check', 'Only approved provider and current announced fee', 'Official/conditional'],
      ['Visa/KVAC', 'Verify current cohort notice', 'Official/conditional'],
      ['Job guarantee fee', 'No official basis in EPS employer selection', 'High risk'],
    ];
    return Scaffold(
      appBar: AppBar(title: const Text('Official Cost Ledger')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('Pay only after checking the current official source.',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          ...costs.map((c) => Card(
                child: ListTile(
                  title: Text(c[0]),
                  subtitle: Text('${c[1]}\nStatus: ${c[2]}'),
                  isThreeLine: true,
                ),
              )),
        ],
      ),
    );
  }
}