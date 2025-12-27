import { Routes, Route } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { Layout } from './components/Layout'
import { ChatPage } from './pages/ChatPage'
import { SharedView } from './pages/SharedView'
import { useUIStore } from './stores/uiStore'
import { PWAInstallPrompt } from './components/PWAInstallPrompt'
import { OfflineIndicator } from './components/OfflineIndicator'
import { useOnlineStatus } from './hooks/useOnlineStatus'
import { useSessionTimeout } from './hooks/useSessionTimeout'
import { SessionTimeoutModal } from './components/SessionTimeoutModal'

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
    <>
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
    </>
  )
}

export default App
