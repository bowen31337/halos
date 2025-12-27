import { Routes, Route } from 'react-router-dom'
import { useEffect, useState, Suspense, lazy } from 'react'
import { useUIStore } from './stores/uiStore'
import { OfflineIndicator } from './components/OfflineIndicator'
import { useOnlineStatus } from './hooks/useOnlineStatus'
import { useSessionTimeout } from './hooks/useSessionTimeout'
import { SessionTimeoutModal } from './components/SessionTimeoutModal'

// Lazy load heavy components for code splitting
const Layout = lazy(() => import('./components/Layout').then(m => ({ default: m.Layout })))
const ChatPage = lazy(() => import('./pages/ChatPage').then(m => ({ default: m.ChatPage })))
const SharedView = lazy(() => import('./pages/SharedView').then(m => ({ default: m.SharedView })))
const PWAInstallPrompt = lazy(() => import('./components/PWAInstallPrompt').then(m => ({ default: m.PWAInstallPrompt })))

// Loading fallback component
function LoadingFallback() {
  return (
    <div className="flex items-center justify-center h-screen bg-[var(--bg-primary)]">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--primary)] mx-auto mb-4"></div>
        <div className="text-[var(--text-secondary)]">Loading...</div>
      </div>
    </div>
  )
}

function App() {
  const { theme, setTheme, fontSize, setFontSize, highContrast, setHighContrast, colorBlindMode, setColorBlindMode } = useUIStore()
  const { showWarning, showTimeout, handleSessionReset, handleLogout, handleExtendSession } = useSessionTimeout()
  const [showModal, setShowModal] = useState(false)

  // Monitor online/offline status
  useOnlineStatus()

  // Sync modal visibility with session timeout state
  useEffect(() => {
    setShowModal(showWarning || showTimeout)
  }, [showWarning, showTimeout])

  // Initialize theme on mount
  useEffect(() => {
    setTheme(theme)
  }, [theme, setTheme])

  // Initialize font size on mount
  useEffect(() => {
    setFontSize(fontSize)
  }, [fontSize, setFontSize])

  // Initialize high contrast on mount
  useEffect(() => {
    setHighContrast(highContrast)
  }, [highContrast, setHighContrast])

  // Initialize color blind mode on mount
  useEffect(() => {
    setColorBlindMode(colorBlindMode)
  }, [colorBlindMode, setColorBlindMode])

  return (
    <Suspense fallback={<LoadingFallback />}>
      <OfflineIndicator />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<ChatPage />} />
          <Route path="c/:conversationId" element={<ChatPage />} />
        </Route>
        <Route path="/share/:shareToken" element={<SharedView />} />
      </Routes>
      <PWAInstallPrompt />
      {showModal && (
        <SessionTimeoutModal
          onClose={() => setShowModal(false)}
          onExtendSession={async () => {
            await handleExtendSession()
            setShowModal(false)
          }}
          onLogout={async () => {
            await handleLogout()
            setShowModal(false)
          }}
        />
      )}
    </Suspense>
  )
}

export default App
