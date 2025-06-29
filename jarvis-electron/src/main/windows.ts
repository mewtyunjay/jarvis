import { BrowserWindow, screen, app } from 'electron'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
import { existsSync } from 'fs'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

export function createMainWindow(): BrowserWindow {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize
  
  const isDev = !app.isPackaged
  const preloadPath = isDev 
    ? join(__dirname, '../preload/preload.js')
    : join(__dirname, '../preload/preload.js')
  
  console.log('Main: isDev:', isDev)
  console.log('Main: Preload script path:', preloadPath)
  console.log('Main: __dirname:', __dirname)
  console.log('Main: Preload file exists:', existsSync(preloadPath))
  
  const mainWindow = new BrowserWindow({
    width: Math.min(1400, width - 100),
    height: Math.min(900, height - 100),
    minWidth: 1000,
    minHeight: 700,
    show: false,
    autoHideMenuBar: true,
    title: 'Jarvis',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: preloadPath,
      webSecurity: true,
      allowRunningInsecureContent: false
    },
    icon: process.platform === 'linux' ? join(__dirname, '../../assets/icon.png') : undefined
  })

  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.on('close', (event) => {
    if (process.platform === 'darwin') {
      event.preventDefault()
      mainWindow.hide()
    }
  })

  return mainWindow
}