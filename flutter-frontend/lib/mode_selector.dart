import 'package:flutter/material.dart';

class ModeSelector extends StatefulWidget {
  final Function(String) onModeChanged;
  const ModeSelector({super.key, required this.onModeChanged});

  @override
  State<ModeSelector> createState() => _ModeSelectorState();
}

class _ModeSelectorState extends State<ModeSelector> {
  String mode = 'app';

  @override
  Widget build(BuildContext context) {
    return Positioned(
      top: 32,
      right: 32,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: Colors.black.withOpacity(0.7),
          borderRadius: BorderRadius.circular(12),
          boxShadow: [BoxShadow(color: Colors.amber, blurRadius: 12)],
        ),
        child: Row(
          children: [
            const Text('Mode:', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            const SizedBox(width: 8),
            DropdownButton<String>(
              value: mode,
              dropdownColor: Colors.black,
              style: const TextStyle(color: Colors.amber, fontWeight: FontWeight.bold),
              items: const [
                DropdownMenuItem(value: 'app', child: Text('App')),
                DropdownMenuItem(value: 'launcher', child: Text('Launcher')),
              ],
              onChanged: (value) {
                if (value != null) {
                  setState(() => mode = value);
                  widget.onModeChanged(value);
                }
              },
            ),
          ],
        ),
      ),
    );
  }
}
