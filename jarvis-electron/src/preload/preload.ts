import { contextBridge, ipcRenderer } from 'electron'

export interface ElectronAPI {
  app: {
    getVersion: () => Promise<string>
    getName: () => Promise<string>
  }
  websocket: {
    connect: (url: string) => Promise<{ success: boolean; message: string }>
    disconnect: () => Promise<{ success: boolean; message: string }>
    send: (message: any) => Promise<{ success: boolean; message: string }>
  }
  logger: {
    log: (level: string, message: string) => void
  }
}

const electronAPI: ElectronAPI = {
  app: {
    getVersion: () => ipcRenderer.invoke('app:getVersion'),
    getName: () => ipcRenderer.invoke('app:getName')
  },
  websocket: {
    connect: (url: string) => ipcRenderer.invoke('websocket:connect', url),
    disconnect: () => ipcRenderer.invoke('websocket:disconnect'),
    send: (message: any) => ipcRenderer.invoke('websocket:send', message)
  },
  logger: {
    log: (level: string, message: string) => ipcRenderer.send('log', level, message)
  }
}

contextBridge.exposeInMainWorld('electronAPI', electronAPI)

declare global {
  interface Window {
    electronAPI: ElectronAPI
  }
}