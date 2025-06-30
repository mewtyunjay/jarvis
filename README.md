# Jarvis AI Assistant

**Work in Progress**

A full-stack AI assistant application built with Electron frontend and Python FastAPI backend. The assistant provides a desktop interface for AI-powered conversations and task automation.

## Architecture

- **Frontend**: Electron desktop application with React and TypeScript
- **Backend**: FastAPI server with OpenAI Agents SDK (for now)

## Quick Start

1. Start the backend:
   ```bash
   cd jarvis-backend
   uv run python main.py
   ```

2. Start the frontend:
   ```bash
   cd jarvis-electron
   npm install
   npm run dev:electron
   ```

## Status

This project is currently under active development. Core WebSocket communication between frontend and backend is implemented and working.