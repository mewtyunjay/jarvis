import { contextBridge, ipcRenderer } from 'electron'

export interface ElectronAPI {
  test: {
    ping: () => Promise<{ success: boolean; message: string }>
  }
  app: {
    getVersion: () => Promise<string>
    getName: () => Promise<string>
  }
  websocket: {
    connect: (url: string) => Promise<{ success: boolean; message: string }>
    disconnect: () => Promise<{ success: boolean; message: string }>
    send: (message: any) => Promise<{ success: boolean; message: string }>
    onMessage: (callback: (message: string) => void) => void
    offMessage: (callback: (message: string) => void) => void
  }
  logger: {
    log: (level: string, message: string) => void
  }
}

const electronAPI: ElectronAPI = {
  test: {
    ping: () => ipcRenderer.invoke('test:ping')
  },
  app: {
    getVersion: () => ipcRenderer.invoke('app:getVersion'),
    getName: () => ipcRenderer.invoke('app:getName')
  },
  websocket: {
    connect: (url: string) => {
      console.log('Preload: websocket.connect called with url:', url)
      const result = ipcRenderer.invoke('websocket:connect', url)
      console.log('Preload: ipcRenderer.invoke result:', result)
      return result
    },
    disconnect: () => ipcRenderer.invoke('websocket:disconnect'),
    send: (message: any) => ipcRenderer.invoke('websocket:send', message),
    onMessage: (callback: (message: string) => void) => {
      ipcRenderer.on('websocket:message', (_, message: string) => callback(message))
    },
    offMessage: (_callback: (message: string) => void) => {
      ipcRenderer.removeAllListeners('websocket:message')
    }
  },
  logger: {
    log: (level: string, message: string) => ipcRenderer.send('log', level, message)
  }
}

console.log('Preload: Script loaded, exposing electronAPI to main world')
console.log('Preload: electronAPI object:', electronAPI)

try {
  contextBridge.exposeInMainWorld('electronAPI', electronAPI)
  console.log('Preload: electronAPI exposed successfully')
} catch (error) {
  console.error('Preload: Failed to expose electronAPI:', error)
}

// Test if it was exposed
setTimeout(() => {
  console.log('Preload: Checking if electronAPI was exposed...')
}, 100)

declare global {
  interface Window {
    electronAPI: ElectronAPI
  }
}