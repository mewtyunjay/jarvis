import { ipcMain, app, BrowserWindow } from 'electron'
import WebSocket from 'ws'

let wsConnection: WebSocket | null = null

export function setupIPC() {
  console.log('IPC: Setting up IPC handlers...')
  
  // Add a test handler to verify IPC communication
  ipcMain.handle('test:ping', () => {
    console.log('IPC: Ping received from renderer')
    return { success: true, message: 'Pong from main process' }
  })
  
  ipcMain.handle('app:getVersion', () => {
    return app.getVersion()
  })

  ipcMain.handle('app:getName', () => {
    return app.getName()
  })

  ipcMain.handle('websocket:connect', async (_, url: string) => {
    console.log('IPC: Attempting to connect to WebSocket:', url)
    try {
      if (wsConnection) {
        console.log('IPC: Closing existing WebSocket connection')
        wsConnection.close()
      }

      wsConnection = new WebSocket(url)
      console.log('IPC: WebSocket instance created')
      
      return new Promise((resolve) => {
        const timeout = setTimeout(() => {
          console.log('IPC: WebSocket connection timeout')
          if (wsConnection) {
            wsConnection.close()
            wsConnection = null
          }
          resolve({ success: false, message: 'WebSocket connection timeout' })
        }, 10000) // 10 second timeout

        wsConnection!.on('open', () => {
          clearTimeout(timeout)
          console.log('IPC: WebSocket connected successfully to:', url)
          resolve({ success: true, message: 'Connected to WebSocket' })
        })

        wsConnection!.on('message', (data) => {
          const message = data.toString()
          console.log('IPC: WebSocket message received:', message)
          
          const mainWindow = BrowserWindow.getAllWindows()[0]
          if (mainWindow) {
            mainWindow.webContents.send('websocket:message', message)
          }
        })

        wsConnection!.on('error', (error) => {
          clearTimeout(timeout)
          console.error('IPC: WebSocket error:', error)
          console.error('IPC: WebSocket error details:', {
            message: error.message,
            code: (error as any).code,
            errno: (error as any).errno,
            syscall: (error as any).syscall,
            address: (error as any).address,
            port: (error as any).port
          })
          wsConnection = null
          resolve({ success: false, message: `WebSocket connection failed: ${error.message}` })
        })

        wsConnection!.on('close', (code, reason) => {
          clearTimeout(timeout)
          console.log('IPC: WebSocket connection closed, code:', code, 'reason:', reason?.toString())
          wsConnection = null
          // Don't resolve here unless it's an unexpected close
        })
      })
    } catch (error) {
      console.error('IPC: WebSocket connection failed:', error)
      return { success: false, message: (error as Error).message }
    }
  })

  ipcMain.handle('websocket:disconnect', async () => {
    if (wsConnection) {
      wsConnection.close()
      wsConnection = null
      return { success: true, message: 'WebSocket disconnected' }
    }
    return { success: true, message: 'No WebSocket connection to disconnect' }
  })

  ipcMain.handle('websocket:send', async (_, message: any) => {
    if (!wsConnection || wsConnection.readyState !== WebSocket.OPEN) {
      return { success: false, message: 'WebSocket is not connected' }
    }

    try {
      wsConnection.send(JSON.stringify(message))
      console.log('WebSocket message sent:', message)
      return { success: true, message: 'Message sent successfully' }
    } catch (error) {
      console.error('WebSocket send failed:', error)
      return { success: false, message: (error as Error).message }
    }
  })

  ipcMain.on('log', (_, level: string, message: string) => {
    console.log(`[${level.toUpperCase()}] ${message}`)
  })
}