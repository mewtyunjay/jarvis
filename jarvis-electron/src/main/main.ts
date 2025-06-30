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
  
  // Check if Vite dev server is running
  let isViteRunning = false
  if (isDev) {
    try {
      const response = await fetch('http://localhost:5173')
      isViteRunning = response.ok
    } catch {
      isViteRunning = false
    }
  }
  
  if (isDev && isViteRunning) {
    console.log('Main: Development mode - loading from Vite dev server')
    await mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
  } else {
    console.log('Main: Production mode - loading built files from:', join(__dirname, '../renderer/index.html'))
    await mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })

  return mainWindow
}

app.whenReady().then(() => {
  console.log('Main: App ready, creating window...')
  createWindow()
  console.log('Main: Setting up IPC...')
  setupIPC()
  console.log('Main: Creating tray...')
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