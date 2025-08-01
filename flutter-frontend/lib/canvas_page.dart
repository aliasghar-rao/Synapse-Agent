// canvas_page.dart: Flutter Canvas UI for Agent Flows
import 'package:flutter/material.dart';
// import 'package:web_socket_channel/web_socket_channel.dart'; // Uncomment if using WebSocket

class CanvasNode {
  final String id;
  final String type;
  final Offset position;
  CanvasNode({required this.id, required this.type, required this.position});
}

class CanvasEdge {
  final String source;
  final String target;
  CanvasEdge({required this.source, required this.target});
}

class CanvasPage extends StatefulWidget {
  @override
  _CanvasPageState createState() => _CanvasPageState();
}

class _CanvasPageState extends State<CanvasPage> {
  // late WebSocketChannel channel;
  List<CanvasNode> nodes = [];
  List<CanvasEdge> edges = [];
  String executionStatus = 'idle';

  @override
  void initState() {
    super.initState();
    // channel = WebSocketChannel.connect(Uri.parse('ws://localhost:8000/canvas-ws'));
  }

  void executeCanvas() async {
    setState(() => executionStatus = 'running');
    // TODO: Send canvas data to backend and listen for updates
    await Future.delayed(const Duration(seconds: 2));
    setState(() => executionStatus = 'idle');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Agent Canvas')),
      body: Stack([
        // TODO: Replace with a custom canvas widget
        Center(child: Text('Canvas UI Here')),
        Positioned(
          bottom: 32,
          right: 32,
          child: FloatingActionButton(
            onPressed: executionStatus == 'running' ? null : executeCanvas,
            child: Icon(executionStatus == 'running' ? Icons.hourglass_empty : Icons.play_arrow),
          ),
        ),
      ]),
    );
  }
}
