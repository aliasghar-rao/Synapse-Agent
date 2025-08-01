# Flutter Frontend for Synapses Agentic Launcher

This is a cross-platform Flutter frontend that can connect to any backend with the same API specs as your current system. It supports Android, iOS, Web, Windows, Linux, and macOS.

## Features
- Responsive UI for mobile, desktop, and web
- Easily configurable backend URL
- Role-based access (admin/user)
- Foldable and dual-screen support (where available)
- Can be attached to any backend with matching API

## Getting Started
1. Install Flutter: https://docs.flutter.dev/get-started/install
2. Run `flutter pub get` in this folder
3. Update `lib/config.dart` with your backend URL
4. Run with `flutter run` (choose your platform)

## Folder Structure
- `lib/` - Main source code
- `assets/` - Images and static files
- `test/` - Unit and widget tests

## API Spec
This frontend expects the backend to provide endpoints for:
- Authentication (login, logout, roles)
- Dashboard data
- Tasks, Notes, Templates, Agents, Settings
- WebSocket for real-time updates (optional)

## Customization
You can easily adapt this frontend for any backend with similar endpoints by updating the API models and config.
