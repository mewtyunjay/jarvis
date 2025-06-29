# Jarvis Electron Frontend

A modern Electron desktop application that serves as the frontend client for the Jarvis AI Assistant. Built with Vite, React, TypeScript, and Tailwind CSS.

## Tech Stack

- **Electron** - Desktop application framework
- **Vite** - Fast development and build tool
- **React 18** - UI library with TypeScript
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Modern UI components
- **Zustand** - Lightweight state management
- **electron-builder** - Application packaging and distribution

## Features

- 🎨 Modern, responsive UI with custom title bar
- 🌙 Dark/light theme support
- 💬 Chat interface for AI interaction
- 🔌 WebSocket client for backend communication
- 📁 Project and file context management
- 📊 Real-time agent status monitoring
- 🔧 System tray integration
- 📱 Cross-platform support (macOS, Windows, Linux)

## Project Structure

```
jarvis-electron/
├── src/
│   ├── main/           # Main process (Node.js/Electron)
│   │   ├── main.ts     # Application entry point
│   │   ├── windows.ts  # Window management
│   │   ├── ipc.ts      # IPC handlers
│   │   └── tray.ts     # System tray
│   ├── renderer/       # Renderer process (React)
│   │   ├── src/
│   │   │   ├── components/  # React components
│   │   │   ├── stores/      # Zustand stores
│   │   │   ├── hooks/       # Custom React hooks
│   │   │   └── types/       # TypeScript types
│   │   ├── index.html
│   │   └── main.tsx
│   └── preload/
│       └── preload.ts  # Secure IPC bridge
├── dist/               # Build output
├── build/              # Build assets and configuration
└── release/            # Distribution packages
```

## Prerequisites

- Node.js 18+ and npm
- Python backend (separate repository)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd jarvis-electron
```

2. Install dependencies:
```bash
npm install
```

## Development

### Start Development Server

```bash
npm run dev
```

This will:
- Start the Vite development server on `http://localhost:5173`
- Launch Electron with hot reload enabled
- Open developer tools automatically

### Development Scripts

- `npm run dev` - Start development with hot reload
- `npm run electron:dev` - Alternative development command
- `npm run electron` - Run Electron without dev server

## Building

### Build for Development Testing

```bash
npm run preview
```

### Build for Production

```bash
npm run build
```

This compiles:
- Main process TypeScript → `dist/main/`
- Preload script → `dist/preload/`
- Renderer React app → `dist/renderer/`

### Create Distribution Package

```bash
npm run dist
```

Creates platform-specific installers in `release/` directory:
- **macOS**: `.dmg` and `.zip` files
- **Windows**: `.exe` installer and portable `.exe`
- **Linux**: `.AppImage`, `.deb`, and `.rpm` packages

## Configuration

### Backend Connection

The app connects to a Python backend via WebSocket. Default configuration:
- **URL**: `ws://localhost:8000/ws`
- **Auto-connect**: Enabled
- **Reconnection**: Automatic with 5-second delay

Configure in the app settings or modify `src/renderer/src/stores/appStore.ts`.

### Window Settings

Default window configuration:
- **Size**: 1400x900px (minimum 1000x700px)
- **Title Bar**: Custom/hidden
- **System Tray**: Enabled
- **Always on Top**: Optional

## Architecture

### Multi-Process Structure

1. **Main Process** (`src/main/`)
   - Manages application lifecycle
   - Creates and controls windows
   - Handles system tray
   - Provides secure IPC APIs

2. **Renderer Process** (`src/renderer/`)
   - React-based user interface
   - Manages application state with Zustand
   - Communicates with main process via IPC

3. **Preload Script** (`src/preload/`)
   - Secure bridge between main and renderer
   - Context isolation enabled
   - Exposes safe APIs to renderer

### State Management

- **Chat Store**: Conversations and messages
- **App Store**: Settings, agent status, context files
- **Persistent Storage**: Settings and projects saved locally

### Security Features

- Context isolation enabled
- Node integration disabled in renderer
- Secure IPC communication
- No remote module access

## Development Guidelines

### Code Style

- TypeScript strict mode enabled
- ESLint configuration included
- Consistent file naming (camelCase for files, PascalCase for components)

### Adding New Features

1. Create types in `src/renderer/src/types/`
2. Add state management in `src/renderer/src/stores/`
3. Create React components in `src/renderer/src/components/`
4. Add IPC handlers in `src/main/ipc.ts` if needed
5. Update preload script for new APIs

## Troubleshooting

### Common Issues

1. **App won't start**: Check if backend is running
2. **Build fails**: Ensure all dependencies are installed
3. **WebSocket connection fails**: Verify backend URL and port
4. **Hot reload not working**: Restart development server

### Debug Mode

Development builds include:
- Developer tools auto-open
- Verbose logging
- Source maps enabled

### Logs

Application logs are available in:
- **Development**: Browser console and terminal
- **Production**: Platform-specific log directories

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

Built with ❤️ for the Jarvis AI Assistant project.