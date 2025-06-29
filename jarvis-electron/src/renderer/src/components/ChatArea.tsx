import React, { useState } from 'react'
import { Send, Paperclip } from 'lucide-react'

export function ChatArea() {
  const [message, setMessage] = useState('')

  const handleSend = () => {
    if (message.trim()) {
      console.log('Sending message:', message)
      setMessage('')
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex-1 flex flex-col">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto space-y-4">
          {/* Welcome Message */}
          <div className="text-center py-8">
            <h1 className="text-2xl font-bold mb-2">Welcome to Jarvis</h1>
            <p className="text-muted-foreground">
              Your AI assistant is ready to help. Start a conversation below.
            </p>
          </div>
          
          {/* Placeholder Messages */}
          <div className="space-y-4">
            <div className="flex justify-end">
              <div className="bg-primary text-primary-foreground rounded-lg px-4 py-2 max-w-[70%]">
                Hello Jarvis, can you help me with a coding task?
              </div>
            </div>
            
            <div className="flex justify-start">
              <div className="bg-muted rounded-lg px-4 py-2 max-w-[70%]">
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm font-medium">Jarvis</span>
                </div>
                Hello! I'd be happy to help you with your coding task. What would you like to work on?
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Input Area */}
      <div className="border-t border-border p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-end space-x-2">
            <button className="p-2 hover:bg-accent rounded-lg transition-colors">
              <Paperclip size={20} />
            </button>
            
            <div className="flex-1 relative">
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                className="w-full resize-none rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent min-h-[40px] max-h-32"
                rows={1}
              />
            </div>
            
            <button
              onClick={handleSend}
              disabled={!message.trim()}
              className="p-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}