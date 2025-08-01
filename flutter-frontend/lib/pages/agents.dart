import 'package:flutter/material.dart';

class AgentsPage extends StatelessWidget {
  const AgentsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Synapses Agents')),
      body: Center(child: Text('Agents List Here')),
    );
  }
}
