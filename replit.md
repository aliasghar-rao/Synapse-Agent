# Drive-Manager Pro

## Overview
Drive-Manager Pro is a cross-platform file management application with AI-powered organization and neural link-based visualization. It features a sophisticated mind map interface for file relationships, multi-tiered AI analysis, and comprehensive cloud storage integration across Windows, Linux, macOS, and Android platforms.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture
The application follows a modular architecture with clear separation of concerns:

- **Frontend**: PyQt6-based desktop interface with responsive design for mobile
- **Backend**: Python modules handling file operations, AI analysis, and cloud integration
- **Database**: SQLAlchemy ORM with support for multiple database backends
- **AI Processing**: Multi-tiered approach (local → remote → cloud) for file analysis
- **Platform Abstraction**: Platform-specific optimizations for different operating systems

## Key Components

### User Interface
- **Mind Map Component**: Neural network visualization using NetworkX and Matplotlib
- **Three-Panel Layout**: AI Analysis, Cloud Storage, and Tools sections
- **Responsive Design**: Adaptive layout for desktop and mobile platforms
- **Platform-Specific Styling**: Fluent Design (Windows), Material Design (Android), native styling (macOS/Linux)

### File Management System
- **File System Manager**: Core file operations and metadata collection
- **Duplicate Detection**: SHA-256 hash-based duplicate file identification
- **Media Handler**: Advanced processing for images, videos, audio, and documents
- **Cross-Platform Support**: Platform-specific file system optimizations

### AI Analysis Engine
- **Multi-Tiered Processing**: Local lightweight models, remote server processing, cloud API integration
- **Intelligent Tagging**: Automated file categorization and relationship detection
- **Recommendation System**: Daily suggestions for file organization and cleanup
- **Media Generation**: AI-powered image and video creation using Ollama

### Cloud Integration
- **Multi-Provider Support**: Google Drive, Dropbox, OneDrive, Box integration
- **Sync Management**: Real-time synchronization status and conflict resolution
- **Offline Capabilities**: Local caching and queued operations

### Application Management
- **APK System**: Android app creation, analysis, and extraction
- **Template Engine**: Reusable app templates and UI component extraction
- **Module Manager**: Dynamic feature enabling/disabling

## Data Flow
1. **File Discovery**: Platform-specific file system scanning
2. **Metadata Extraction**: File properties, hashes, and relationships
3. **AI Analysis**: Multi-tiered processing for tagging and recommendations
4. **Database Storage**: Persistent storage of file metadata and relationships
5. **UI Updates**: Real-time updates to mind map and interface panels
6. **Cloud Sync**: Bidirectional synchronization with cloud providers

## External Dependencies
- **PyQt6**: Desktop GUI framework
- **SQLAlchemy**: Database ORM
- **NetworkX**: Graph processing for mind map
- **Matplotlib**: Data visualization
- **Pillow**: Image processing
- **OpenCV**: Computer vision (optional)
- **Requests**: HTTP client for API calls
- **Ollama**: Local AI model integration

## Deployment Strategy
- **Desktop Platforms**: Native installers for Windows, macOS, and Linux
- **Android**: APK package with platform-specific optimizations
- **Web Demo**: Simplified web interface for demonstration
- **Modular Installation**: Optional components based on available dependencies
- **Cross-Platform Compatibility**: Graceful degradation when optional dependencies are missing

The architecture prioritizes modularity, allowing features to be enabled/disabled based on platform capabilities and user preferences. The multi-tiered AI approach ensures functionality across different hardware configurations while maintaining performance and user experience.