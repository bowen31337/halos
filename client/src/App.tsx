import { Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import { Layout } from './components/Layout'
import { ChatPage } from './pages/ChatPage'
import { useUIStore } from './stores/uiStore'

function App() {
  const { theme, setTheme } = useUIStore()

  // Initialize theme on mount
  useEffect(() => {
    setTheme(theme)
  }, [theme, setTheme])

  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<ChatPage />} />
        <Route path="c/:conversationId" element={<ChatPage />} />
      </Route>
    </Routes>
  )
}

export default App
