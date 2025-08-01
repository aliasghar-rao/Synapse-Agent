import 'package:flutter/material.dart';
import 'config.dart';
import 'routes.dart';


import 'mode_selector.dart';

void main() {
  runApp(const SynapsesLauncherApp());
}

class SynapsesLauncherApp extends StatefulWidget {
  const SynapsesLauncherApp({super.key});

  @override
  State<SynapsesLauncherApp> createState() => _SynapsesLauncherAppState();
}

class _SynapsesLauncherAppState extends State<SynapsesLauncherApp> {
  String mode = 'app';

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Synapses Launcher',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      initialRoute: '/',
      routes: appRoutes,
      builder: (context, child) {
        return Stack(
          children: [
            child ?? Container(),
            ModeSelector(onModeChanged: (m) => setState(() => mode = m)),
            if (mode == 'launcher')
              Positioned(
                bottom: 40,
                left: 40,
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.7),
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [BoxShadow(color: Colors.amber, blurRadius: 16)],
                  ),
                  child: const Text(
                    'Launcher Mode Active',
                    style: TextStyle(color: Colors.amber, fontWeight: FontWeight.bold, fontSize: 18),
                  ),
                ),
              ),
          ],
        );
      },
    );
  }
}
