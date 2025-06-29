import { useEffect, useRef, useState } from 'react'
import { useAppStore } from '../stores/appStore'

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const { settings, setAgentStatus } = useAppStore()
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()

  const connect = async () => {
    if (isConnecting) return

    setIsConnecting(true)
    setAgentStatus({ backend: 'connecting' })

    try {
      const result = await window.electronAPI?.websocket.connect(settings.backendUrl)
      
      if (result?.success) {
        setIsConnected(true)
        setAgentStatus({ 
          connected: true, 
          backend: 'available',
          lastPing: new Date()
        })
        window.electronAPI?.logger.log('info', 'WebSocket connected successfully')
      } else {
        throw new Error(result?.message || 'Connection failed')
      }
    } catch (error) {
      console.error('WebSocket connection failed:', error)
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