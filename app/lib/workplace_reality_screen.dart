import 'package:flutter/material.dart';

class WorkplaceRealityScreen extends StatelessWidget {
  const WorkplaceRealityScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final checks = const [
      ['Company identity', 'Business name, address, industry, existence'],
      ['Location reality', 'Map, public transport, nearby hospital and stores'],
      ['Accommodation', 'Dormitory type, cost, occupancy when verified'],
      ['Worker evidence', 'Verified-worker structured feedback'],
      ['Contract vs reality', 'Payday, overtime, shifts, deductions, commute'],
      ['Physical verification', 'Optional local scout visit with permission'],
    ];
    return Scaffold(
      appBar: AppBar(title: const Text('Workplace Reality Check')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('Know the workplace before you commit.', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          ...checks.map((c) => Card(
                child: ListTile(title: Text(c[0]), subtitle: Text(c[1])),
              )),
          const SizedBox(height: 16),
          FilledButton.tonal(onPressed: null, child: Text('Request physical verification (coming next)')),
        ],
      ),
    );
  }
}