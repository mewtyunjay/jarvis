import React, { useState, useEffect } from 'react'
import { Send, Paperclip } from 'lucide-react'
import { useChatStore } from '../stores/chatStore'
import { useWebSocket } from '../hooks/useWebSocket'

export function ChatArea() {
  const [message, setMessage] = useState('')
  const { 
    conversations, 
    activeConversationId, 
    createConversation, 
    addMessage, 
    isLoading,
    setLoading 
  } = useChatStore()
  const { isConnected, send } = useWebSocket()

  const activeConversation = conversations.find(c => c.id === activeConversationId)

  const handleSend = async () => {
    if (!message.trim() || !isConnected) return

    let conversationId = activeConversationId
    if (!conversationId) {
      conversationId = createConversation()
    }

    addMessage(conversationId, {
      role: 'user',
      content: message.trim()
    })

    const userMessage = message.trim()
    setMessage('')
    setLoading(true)

    try {
      await send({
        type: 'user_message',
        content: userMessage
      })
    } catch (error) {
      console.error('Failed to send message:', error)
      addMessage(conversationId, {
        role: 'assistant',
        content: 'Sorry, I encountered an error while processing your message.'
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const handleWebSocketMessage = (message: string) => {
      try {
        const data = JSON.parse(message)
        if (data.type === 'assistant_message' && activeConversationId) {
          addMessage(activeConversationId, {
            role: 'assistant',
            content: data.content
          })
          setLoading(false)
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    window.electronAPI?.websocket.onMessage(handleWebSocketMessage)
    
    return () => {
      window.electronAPI?.websocket.offMessage(handleWebSocketMessage)
    }
  }, [activeConversationId, addMessage, setLoading])

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
          {activeConversation && activeConversation.messages.length > 0 ? (
            <div className="space-y-4">
              {activeConversation.messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`rounded-lg px-4 py-2 max-w-[70%] ${
                      msg.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    }`}
                  >
                    {msg.role === 'assistant' && (
                      <div className="flex items-center space-x-2 mb-2">
                        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                        <span className="text-sm font-medium">Jarvis</span>
                      </div>
                    )}
                    {msg.content}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-muted rounded-lg px-4 py-2 max-w-[70%]">
                    <div className="flex items-center space-x-2 mb-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                      <span className="text-sm font-medium">Jarvis</span>
                    </div>
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-current rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <h1 className="text-2xl font-bold mb-2">Welcome to Jarvis</h1>
              <p className="text-muted-foreground">
                {isConnected ? 'Your AI assistant is ready to help. Start a conversation below.' : 'Connecting to Jarvis...'}
              </p>
            </div>
          )}
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
              disabled={!message.trim() || !isConnected || isLoading}
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