export interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: Date
  status?: 'sending' | 'sent' | 'error'
}

export interface Conversation {
  id: string
  title: string
  messages: Message[]
  createdAt: Date
  updatedAt: Date
}

export interface Project {
  id: string
  name: string
  path: string
  files: string[]
  createdAt: Date
}

export interface ContextFile {
  id: string
  name: string
  path: string
  content?: string
  type: 'text' | 'image' | 'document'
  size: number
}

export interface AgentStatus {
  connected: boolean
  backend: 'available' | 'unavailable' | 'connecting'
  model?: string
  lastPing?: Date
}

export interface AppSettings {
  theme: 'light' | 'dark' | 'system'
  backendUrl: string
  autoConnect: boolean
  windowSettings: {
    alwaysOnTop: boolean
    minimizeToTray: boolean
  }
}