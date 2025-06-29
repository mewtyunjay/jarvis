import { ipcMain, app } from 'electron'

export function setupIPC() {
  ipcMain.handle('app:getVersion', () => {
    return app.getVersion()
  })

  ipcMain.handle('app:getName', () => {
    return app.getName()
  })

  ipcMain.handle('websocket:connect', async (_, url: string) => {
    console.log('WebSocket connect request:', url)
    return { success: true, message: 'WebSocket connection placeholder' }
  })

  ipcMain.handle('websocket:disconnect', async () => {
    return { success: true, message: 'WebSocket disconnection placeholder' }
  })

  ipcMain.handle('websocket:send', async (_, message: any) => {
    console.log('WebSocket send request:', message)
    return { success: true, message: 'Message send placeholder' }
  })

  ipcMain.on('log', (_, level: string, message: string) => {
    console.log(`[${level.toUpperCase()}] ${message}`)
  })
}