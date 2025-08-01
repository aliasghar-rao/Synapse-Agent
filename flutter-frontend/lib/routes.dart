import 'package:flutter/material.dart';
import 'pages/dashboard.dart';
import 'pages/tasks.dart';
import 'pages/notes.dart';
import 'pages/settings.dart';
import 'pages/templates.dart';
import 'pages/agents.dart';
import 'pages/login.dart';
import 'canvas_page.dart';

Map<String, WidgetBuilder> appRoutes = {
  '/': (context) => const LoginPage(),
  '/dashboard': (context) => const DashboardPage(),
  '/tasks': (context) => const TasksPage(),
  '/notes': (context) => const NotesPage(),
  '/settings': (context) => const SettingsPage(),
  '/templates': (context) => const TemplatesPage(),
  '/agents': (context) => const AgentsPage(),
  '/canvas': (context) => CanvasPage(),
};
