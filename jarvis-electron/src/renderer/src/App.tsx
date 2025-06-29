import React, { useEffect } from 'react'
import { Sidebar } from './components/Sidebar'
import { ChatArea } from './components/ChatArea'
import { RightPanel } from './components/RightPanel'
import { StatusBar } from './components/StatusBar'
import { useWebSocket } from './hooks/useWebSocket'

function App() {
  const { connect } = useWebSocket()

  useEffect(() => {
    // Debug: Check if electronAPI is available
    console.log('App: electronAPI available?', !!window.electronAPI)
    console.log('App: window.electronAPI:', window.electronAPI)
    if (window.electronAPI) {
      console.log('App: electronAPI methods:', Object.keys(window.electronAPI))
      console.log('App: websocket methods:', Object.keys(window.electronAPI.websocket || {}))
      
      // Test basic IPC first
      console.log('App: Testing IPC with getVersion...')
      const versionPromise = window.electronAPI.app.getVersion()
      console.log('App: getVersion returned:', versionPromise)
      
      if (versionPromise && typeof versionPromise.then === 'function') {
        versionPromise.then(version => {
          console.log('App: IPC test successful, app version:', version)
          console.log('App: Now testing WebSocket IPC call...')
          // Now try WebSocket connection
          connect()
        }).catch(error => {
          console.error('App: IPC test failed:', error)
        })
      } else {
        console.error('App: getVersion did not return a promise, got:', versionPromise)
      }
    } else {
      console.error('App: electronAPI not available, cannot connect to WebSocket')
    }
  }, [])
  return (
    <div className="h-screen bg-background text-foreground flex flex-col">
      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar />
        
        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          <ChatArea />
        </div>
        
        {/* Right Panel */}
        <RightPanel />
      </div>
      
      {/* Status Bar */}
      <StatusBar />
    </div>
  )
}

export default App