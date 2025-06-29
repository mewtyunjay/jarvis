import React, { useState, useEffect } from 'react'
import { Wifi, WifiOff, Circle } from 'lucide-react'
import { useAppStore } from '../stores/appStore'
import { useWebSocket } from '../hooks/useWebSocket'

export function StatusBar() {
  const [appVersion, setAppVersion] = useState<string>('')
  const { agentStatus } = useAppStore()
  const { isConnected } = useWebSocket()

  useEffect(() => {
    if (window.electronAPI) {
      window.electronAPI.app.getVersion().then(setAppVersion)
    }
  }, [])

  return (
    <div className="h-6 bg-muted/50 border-t border-border flex items-center justify-between px-4 text-xs text-muted-foreground">
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-1">
          {isConnected ? (
            <Circle size={8} className="fill-green-500 text-green-500" />
          ) : (
            <Circle size={8} className="fill-red-500 text-red-500" />
          )}
          <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
        
        <div className="flex items-center space-x-1">
          {isConnected ? <Wifi size={12} /> : <WifiOff size={12} />}
          <span>WebSocket</span>
        </div>
      </div>
      
      <div className="flex items-center space-x-4">
        <span>{agentStatus.backend === 'connecting' ? 'Connecting...' : 'Ready'}</span>
        {appVersion && <span>v{appVersion}</span>}
      </div>
    </div>
  )
}