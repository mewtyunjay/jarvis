import React, { useState } from 'react'
import { ChevronLeft, ChevronRight, FileText, Activity, Database } from 'lucide-react'

export function RightPanel() {
  const [isCollapsed, setIsCollapsed] = useState(false)

  if (isCollapsed) {
    return (
      <div className="w-8 bg-muted/30 border-l border-border flex flex-col">
        <button
          onClick={() => setIsCollapsed(false)}
          className="p-2 hover:bg-accent transition-colors"
        >
          <ChevronLeft size={16} />
        </button>
      </div>
    )
  }

  return (
    <div className="w-80 bg-muted/30 border-l border-border flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border flex items-center justify-between">
        <h2 className="text-sm font-semibold">Context & Status</h2>
        <button
          onClick={() => setIsCollapsed(true)}
          className="p-1 hover:bg-accent rounded transition-colors"
        >
          <ChevronRight size={16} />
        </button>
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Agent Status */}
        <div className="p-4 border-b border-border">
          <div className="flex items-center space-x-2 mb-3">
            <Activity size={16} />
            <h3 className="text-sm font-medium">Agent Status</h3>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Connection</span>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                <span>Disconnected</span>
              </div>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Backend</span>
              <span>Not Available</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Model</span>
              <span>-</span>
            </div>
          </div>
        </div>
        
        {/* Context Files */}
        <div className="p-4 border-b border-border">
          <div className="flex items-center space-x-2 mb-3">
            <FileText size={16} />
            <h3 className="text-sm font-medium">Context Files</h3>
          </div>
          <div className="space-y-2">
            <div className="text-xs text-muted-foreground text-center py-4">
              No files in context
            </div>
          </div>
        </div>
        
        {/* Memory/Knowledge */}
        <div className="p-4">
          <div className="flex items-center space-x-2 mb-3">
            <Database size={16} />
            <h3 className="text-sm font-medium">Memory</h3>
          </div>
          <div className="space-y-2">
            <div className="text-xs text-muted-foreground">
              <div className="bg-muted rounded p-2">
                <div className="font-medium mb-1">Session Info</div>
                <div>Started: {new Date().toLocaleTimeString()}</div>
                <div>Messages: 0</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}