import React from 'react'
import { MessageSquare, FolderOpen, Plus, Settings } from 'lucide-react'

export function Sidebar() {
  return (
    <div className="w-64 bg-muted/30 border-r border-border flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold">Conversations</h2>
          <button className="p-1 hover:bg-accent rounded transition-colors">
            <Plus size={16} />
          </button>
        </div>
      </div>
      
      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto p-2">
        <div className="space-y-1">
          {/* Placeholder conversations */}
          {[1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className="p-3 rounded-lg hover:bg-accent cursor-pointer transition-colors"
            >
              <div className="flex items-center space-x-3">
                <MessageSquare size={16} className="text-muted-foreground" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">
                    Conversation {i}
                  </div>
                  <div className="text-xs text-muted-foreground truncate">
                    Last message preview...
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Footer */}
      <div className="p-4 border-t border-border space-y-2">
        <button className="w-full flex items-center space-x-3 p-2 rounded-lg hover:bg-accent transition-colors text-left">
          <FolderOpen size={16} />
          <span className="text-sm">Projects</span>
        </button>
        <button className="w-full flex items-center space-x-3 p-2 rounded-lg hover:bg-accent transition-colors text-left">
          <Settings size={16} />
          <span className="text-sm">Settings</span>
        </button>
      </div>
    </div>
  )
}