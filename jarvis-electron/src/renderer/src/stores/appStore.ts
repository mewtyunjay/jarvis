import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { AppSettings, AgentStatus, ContextFile, Project } from '../types'

interface AppState {
  settings: AppSettings
  agentStatus: AgentStatus
  contextFiles: ContextFile[]
  projects: Project[]
  sidebarCollapsed: boolean
  rightPanelCollapsed: boolean
}

interface AppActions {
  updateSettings: (settings: Partial<AppSettings>) => void
  setAgentStatus: (status: Partial<AgentStatus>) => void
  addContextFile: (file: ContextFile) => void
  removeContextFile: (id: string) => void
  clearContextFiles: () => void
  addProject: (project: Project) => void
  removeProject: (id: string) => void
  toggleSidebar: () => void
  toggleRightPanel: () => void
  setSidebarCollapsed: (collapsed: boolean) => void
  setRightPanelCollapsed: (collapsed: boolean) => void
}

type AppStore = AppState & AppActions

const defaultSettings: AppSettings = {
  theme: 'system',
  backendUrl: 'ws://localhost:8000/ws',
  autoConnect: true,
  windowSettings: {
    alwaysOnTop: false,
    minimizeToTray: true
  }
}

const defaultAgentStatus: AgentStatus = {
  connected: false,
  backend: 'unavailable'
}

export const useAppStore = create<AppStore>()(
  devtools(
    persist(
      (set, get) => ({
        settings: defaultSettings,
        agentStatus: defaultAgentStatus,
        contextFiles: [],
        projects: [],
        sidebarCollapsed: false,
        rightPanelCollapsed: false,

        updateSettings: (newSettings) => {
          set((state) => ({
            settings: { ...state.settings, ...newSettings }
          }))
        },

        setAgentStatus: (status) => {
          set((state) => ({
            agentStatus: { ...state.agentStatus, ...status }
          }))
        },

        addContextFile: (file) => {
          set((state) => ({
            contextFiles: [...state.contextFiles, file]
          }))
        },

        removeContextFile: (id) => {
          set((state) => ({
            contextFiles: state.contextFiles.filter((file) => file.id !== id)
          }))
        },

        clearContextFiles: () => {
          set({ contextFiles: [] })
        },

        addProject: (project) => {
          set((state) => ({
            projects: [project, ...state.projects]
          }))
        },

        removeProject: (id) => {
          set((state) => ({
            projects: state.projects.filter((project) => project.id !== id)
          }))
        },

        toggleSidebar: () => {
          set((state) => ({
            sidebarCollapsed: !state.sidebarCollapsed
          }))
        },

        toggleRightPanel: () => {
          set((state) => ({
            rightPanelCollapsed: !state.rightPanelCollapsed
          }))
        },

        setSidebarCollapsed: (collapsed) => {
          set({ sidebarCollapsed: collapsed })
        },

        setRightPanelCollapsed: (collapsed) => {
          set({ rightPanelCollapsed: collapsed })
        }
      }),
      {
        name: 'jarvis-app-store',
        partialize: (state) => ({
          settings: state.settings,
          projects: state.projects,
          sidebarCollapsed: state.sidebarCollapsed,
          rightPanelCollapsed: state.rightPanelCollapsed
        })
      }
    ),
    { name: 'app-store' }
  )
)