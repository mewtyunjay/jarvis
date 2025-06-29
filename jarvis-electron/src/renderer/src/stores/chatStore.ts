import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { Message, Conversation } from '../types'

interface ChatState {
  conversations: Conversation[]
  activeConversationId: string | null
  isLoading: boolean
  error: string | null
}

interface ChatActions {
  createConversation: (title?: string) => string
  setActiveConversation: (id: string) => void
  addMessage: (conversationId: string, message: Omit<Message, 'id' | 'timestamp'>) => void
  updateMessage: (conversationId: string, messageId: string, updates: Partial<Message>) => void
  deleteConversation: (id: string) => void
  clearError: () => void
  setLoading: (loading: boolean) => void
}

type ChatStore = ChatState & ChatActions

export const useChatStore = create<ChatStore>()(
  devtools(
    (set, get) => ({
      conversations: [],
      activeConversationId: null,
      isLoading: false,
      error: null,

      createConversation: (title) => {
        const id = crypto.randomUUID()
        const conversation: Conversation = {
          id,
          title: title || `Conversation ${get().conversations.length + 1}`,
          messages: [],
          createdAt: new Date(),
          updatedAt: new Date()
        }

        set((state) => ({
          conversations: [conversation, ...state.conversations],
          activeConversationId: id
        }))

        return id
      },

      setActiveConversation: (id) => {
        set({ activeConversationId: id })
      },

      addMessage: (conversationId, messageData) => {
        const message: Message = {
          id: crypto.randomUUID(),
          timestamp: new Date(),
          ...messageData
        }

        set((state) => ({
          conversations: state.conversations.map((conv) =>
            conv.id === conversationId
              ? {
                  ...conv,
                  messages: [...conv.messages, message],
                  updatedAt: new Date()
                }
              : conv
          )
        }))
      },

      updateMessage: (conversationId, messageId, updates) => {
        set((state) => ({
          conversations: state.conversations.map((conv) =>
            conv.id === conversationId
              ? {
                  ...conv,
                  messages: conv.messages.map((msg) =>
                    msg.id === messageId ? { ...msg, ...updates } : msg
                  ),
                  updatedAt: new Date()
                }
              : conv
          )
        }))
      },

      deleteConversation: (id) => {
        set((state) => ({
          conversations: state.conversations.filter((conv) => conv.id !== id),
          activeConversationId: state.activeConversationId === id ? null : state.activeConversationId
        }))
      },

      clearError: () => {
        set({ error: null })
      },

      setLoading: (loading) => {
        set({ isLoading: loading })
      }
    }),
    { name: 'chat-store' }
  )
)