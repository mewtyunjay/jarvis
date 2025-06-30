import { useEffect, useRef, useState } from 'react'
import { useAppStore } from '../stores/appStore'

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const { settings, setAgentStatus } = useAppStore()
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()

  const connect = async () => {
    if (isConnecting) return

    console.log('WebSocket: Starting connection to:', settings.backendUrl)
    console.log('WebSocket: Full settings object:', settings)
    console.log('WebSocket: window.electronAPI available:', !!window.electronAPI)
    console.log('WebSocket: window.electronAPI.websocket available:', !!window.electronAPI?.websocket)
    
    // Force IPv4 if localhost is detected
    let connectionUrl = settings.backendUrl
    if (connectionUrl.includes('localhost')) {
      connectionUrl = connectionUrl.replace('localhost', '127.0.0.1')
      console.log('WebSocket: Forcing IPv4, using URL:', connectionUrl)
    }
    
    setIsConnecting(true)
    setAgentStatus({ backend: 'connecting' })

    try {
      console.log('WebSocket: Calling electronAPI.websocket.connect with URL:', connectionUrl)
      const result = await window.electronAPI?.websocket.connect(connectionUrl)
      console.log('WebSocket: Connection result:', result)
      
      if (result?.success) {
        console.log('WebSocket: Connection successful')
        setIsConnected(true)
        setAgentStatus({ 
          connected: true, 
          backend: 'available',
          lastPing: new Date()
        })
        window.electronAPI?.logger.log('info', 'WebSocket connected successfully')
      } else {
        console.log('WebSocket: Connection failed with result:', result)
        throw new Error(result?.message || 'Connection failed')
      }
    } catch (error) {
      console.error('WebSocket: Connection failed with error:', error)
      setIsConnected(false)
      setAgentStatus({ 
        connected: false, 
        backend: 'unavailable'
      })
      window.electronAPI?.logger.log('error', `WebSocket connection failed: ${error}`)
      
      if (settings.autoConnect) {
        scheduleReconnect()
      }
    } finally {
      setIsConnecting(false)
    }
  }

  const disconnect = async () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }

    try {
      await window.electronAPI?.websocket.disconnect()
      setIsConnected(false)
      setAgentStatus({ 
        connected: false, 
        backend: 'unavailable'
      })
      window.electronAPI?.logger.log('info', 'WebSocket disconnected')
    } catch (error) {
      console.error('WebSocket disconnect failed:', error)
    }
  }

  const send = async (message: any) => {
    if (!isConnected) {
      throw new Error('WebSocket is not connected')
    }

    try {
      const result = await window.electronAPI?.websocket.send(message)
      if (!result?.success) {
        throw new Error(result?.message || 'Send failed')
      }
      return result
    } catch (error) {
      console.error('WebSocket send failed:', error)
      throw error
    }
  }

  const scheduleReconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }

    reconnectTimeoutRef.current = setTimeout(() => {
      connect()
    }, 5000) // Retry after 5 seconds
  }

  useEffect(() => {
    if (settings.autoConnect) {
      connect()
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [settings.backendUrl, settings.autoConnect])

  return {
    isConnected,
    isConnecting,
    connect,
    disconnect,
    send
  }
}