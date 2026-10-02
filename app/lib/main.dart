import 'package:flutter/material.dart';
import 'journey_screen.dart';
import 'document_copilot_screen.dart';
import 'cost_ledger_screen.dart';
import 'fee_check_screen.dart';
import 'workplace_reality_screen.dart';

void main() => runApp(const KoreaEmploymentPassport());

class KoreaEmploymentPassport extends StatelessWidget {
  const KoreaEmploymentPassport({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Korea Employment Passport',
      theme: ThemeData(useMaterial3: true),
      home: const HomeShell(),
    );
  }
}

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});
  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int index = 0;
  final pages = const [
    JourneyScreen(),
    DocumentCopilotScreen(),
    CostLedgerScreen(),
    FeeCheckScreen(),
    WorkplaceRealityScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: index, children: pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (value) => setState(() => index = value),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.route), label: 'Journey'),
          NavigationDestination(icon: Icon(Icons.description_outlined), label: 'Docs'),
          NavigationDestination(icon: Icon(Icons.receipt_long_outlined), label: 'Costs'),
          NavigationDestination(icon: Icon(Icons.shield_outlined), label: 'Fee Check'),
          NavigationDestination(icon: Icon(Icons.factory_outlined), label: 'Workplace'),
        ],
      ),
    );
  }
}