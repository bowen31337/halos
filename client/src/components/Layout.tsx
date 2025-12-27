import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { SubAgentIndicator } from './SubAgentIndicator'
import { useUIStore } from '../stores/uiStore'

export function Layout() {
  const { sidebarOpen, sidebarWidth, extendedThinkingEnabled } = useUIStore()

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--bg-primary)]">
      {/* Sidebar */}
      <div
        className={`flex-shrink-0 transition-all duration-300 ease-out ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        style={{ width: sidebarOpen ? sidebarWidth : 0 }}
      >
        <Sidebar />
      </div>

      {/* Main content */}
      <div className="flex flex-1 flex-col min-w-0">
        <Header />
        <main className="flex-1 overflow-hidden">
          <Outlet />
        </main>
      </div>

      {/* Sub-agent indicator - always visible when extended thinking enabled */}
      <SubAgentIndicator
        isVisible={false}
        extendedThinkingEnabled={extendedThinkingEnabled}
      />
    </div>
  )
}
