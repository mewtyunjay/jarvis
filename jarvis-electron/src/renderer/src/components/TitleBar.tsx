import React, { useState, useEffect } from 'react'
import { Minus, Square, X } from 'lucide-react'

export function TitleBar() {
  const [isMaximized, setIsMaximized] = useState(false)

  useEffect(() => {
    checkMaximized()
  }, [])

  const checkMaximized = async () => {
    if (window.electronAPI) {
      const maximized = await window.electronAPI.window.isMaximized()
      setIsMaximized(maximized)
    }
  }

  const handleMinimize = () => {
    window.electronAPI?.window.minimize()
  }

  const handleMaximize = async () => {
    await window.electronAPI?.window.maximize()
    checkMaximized()
  }

  const handleClose = () => {
    window.electronAPI?.window.close()
  }

  return (
    <div className="h-8 bg-background border-b border-border flex items-center justify-between px-4 select-none drag-region">
      <div className="flex items-center space-x-2">
        <div className="w-3 h-3 rounded-full bg-red-500"></div>
        <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
        <div className="w-3 h-3 rounded-full bg-green-500"></div>
        <span className="ml-2 text-sm font-medium">Jarvis</span>
      </div>
      
      <div className="flex items-center space-x-1 no-drag">
        <button
          onClick={handleMinimize}
          className="p-1 hover:bg-accent rounded transition-colors"
          aria-label="Minimize"
        >
          <Minus size={12} />
        </button>
        <button
          onClick={handleMaximize}
          className="p-1 hover:bg-accent rounded transition-colors"
          aria-label={isMaximized ? 'Restore' : 'Maximize'}
        >
          <Square size={12} />
        </button>
        <button
          onClick={handleClose}
          className="p-1 hover:bg-destructive hover:text-destructive-foreground rounded transition-colors"
          aria-label="Close"
        >
          <X size={12} />
        </button>
      </div>
    </div>
  )
}