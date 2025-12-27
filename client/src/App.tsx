import { Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import { Layout } from './components/Layout'
import { ChatPage } from './pages/ChatPage'
import { SharedView } from './pages/SharedView'
import { useUIStore } from './stores/uiStore'

function App() {
  const { theme, setTheme, fontSize, setFontSize } = useUIStore()

  // Initialize theme on mount
  useEffect(() => {
    setTheme(theme)
  }, [theme, setTheme])

  // Initialize font size on mount
  useEffect(() => {
    setFontSize(fontSize)
  }, [fontSize, setFontSize])

  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<ChatPage />} />
        <Route path="c/:conversationId" element={<ChatPage />} />
      </Route>
      <Route path="/share/:shareToken" element={<SharedView />} />
    </Routes>
  )
}

export default App
