import { app, BrowserWindow } from 'electron'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
import { createMainWindow } from './windows.js'
import { setupIPC } from './ipc.js'
import { createTray } from './tray.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const isDev = !app.isPackaged

let mainWindow: BrowserWindow | null = null

async function createWindow() {
  mainWindow = createMainWindow()
  
  if (isDev) {
    // Check if dev server is running
    try {
      await mainWindow.loadURL('http://localhost:5173')
    } catch (error) {
      console.error('Failed to load dev server, loading built files:', error)
      await mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
    }
  } else {
    await mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })

  return mainWindow
}

app.whenReady().then(() => {
  createWindow()
  setupIPC()
  createTray()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  mainWindow?.removeAllListeners('close')
})

export { mainWindow }