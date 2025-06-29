import React from 'react'
import { Sidebar } from './components/Sidebar'
import { ChatArea } from './components/ChatArea'
import { RightPanel } from './components/RightPanel'
import { StatusBar } from './components/StatusBar'

function App() {
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