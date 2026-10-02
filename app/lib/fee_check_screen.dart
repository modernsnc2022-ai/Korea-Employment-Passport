import 'package:flutter/material.dart';

class FeeCheckScreen extends StatefulWidget {
  const FeeCheckScreen({super.key});

  @override
  State<FeeCheckScreen> createState() => _FeeCheckScreenState();
}

class _FeeCheckScreenState extends State<FeeCheckScreen> {
  final controller = TextEditingController();
  String? result;

  void checkFee() {
    final raw = controller.text.replaceAll(RegExp(r'[^0-9]'), '');
    final amount = int.tryParse(raw);
    if (amount == null) {
      setState(() => result = 'Enter an amount in Indonesian rupiah.');
      return;
    }

    if (amount == 350000) {
      setState(() => result = 'Matches the 2026 KP2MI/HIMPSI psychology-test fee. Re-check the current notice before payment.');
    } else if (amount == 1260000) {
      setState(() => result = 'Matches the visa + KVAC admin amount announced from 1 July 2026 for relevant cohorts. Re-check the current notice before payment.');
    } else if (amount >= 1500000 && amount < 1600000) {
      setState(() => result = 'This may be a required minimum BNI account balance, not the visa fee itself. Verify the current notice.');
    } else {
      setState(() => result = 'No exact match in the current verified fee rules. Do not pay until the payee, purpose and official source are verified.');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Check This Fee')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const Text('Enter the amount someone asked you to pay.', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          TextField(
            controller: controller,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Amount (Rp)', border: OutlineInputBorder()),
          ),
          const SizedBox(height: 12),
          FilledButton(onPressed: checkFee, child: const Text('Check fee')),
          if (result != null) ...[
            const SizedBox(height: 20),
            Card(child: Padding(padding: const EdgeInsets.all(16), child: Text(result!))),
          ],
          const SizedBox(height: 20),
          const Text('Rule: amount alone is never enough. The app must also verify the payee, stage and official source.'),
        ],
      ),
    );
  }
}