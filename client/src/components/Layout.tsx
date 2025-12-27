import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { SubAgentIndicator } from './SubAgentIndicator'
import { CommandPalette } from './CommandPalette'
import { OnboardingTour } from './OnboardingTour'
import { useUIStore } from '../stores/uiStore'
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts'
import { useState, useEffect, useRef } from 'react'

export function Layout() {
  const { sidebarOpen, sidebarWidth, setSidebarOpen } = useUIStore()
  const [isMobile, setIsMobile] = useState(false)
  const [isTablet, setIsTablet] = useState(false)
  const location = useLocation()

  // Touch gesture tracking
  const touchStartX = useRef(0)
  const touchStartY = useRef(0)
  const touchStartTime = useRef(0)

  // Initialize global keyboard shortcuts
  useKeyboardShortcuts()

  // Handle responsive breakpoints
  useEffect(() => {
    const checkScreenSize = () => {
      const width = window.innerWidth
      setIsMobile(width < 768)
      setIsTablet(width >= 768 && width < 1024)
    }

    checkScreenSize()
    window.addEventListener('resize', checkScreenSize)
    return () => window.removeEventListener('resize', checkScreenSize)
  }, [])

  // Auto-close sidebar on mobile when navigating
  useEffect(() => {
    if (isMobile && sidebarOpen) {
      setSidebarOpen(false)
    }
    // On tablet, close sidebar when navigating to a conversation
    if (isTablet && sidebarOpen && location.pathname.startsWith('/c/')) {
      setSidebarOpen(false)
    }
  }, [isMobile, isTablet, sidebarOpen, setSidebarOpen, location])

  // Swipe gesture handlers for mobile
  const handleTouchStart = (e: React.TouchEvent) => {
    if (!isMobile) return

    const touch = e.touches[0]
    touchStartX.current = touch.clientX
    touchStartY.current = touch.clientY
    touchStartTime.current = Date.now()
  }

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!isMobile) return

    // Prevent default scrolling if we're doing a horizontal swipe
    const touch = e.touches[0]
    const deltaX = touch.clientX - touchStartX.current
    const deltaY = touch.clientY - touchStartY.current

    // If horizontal movement is greater than vertical, prevent scroll
    if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 10) {
      e.preventDefault()
    }
  }

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (!isMobile) return

    const touch = e.changedTouches[0]
    const deltaX = touch.clientX - touchStartX.current
    const deltaY = touch.clientY - touchStartY.current
    const deltaTime = Date.now() - touchStartTime.current

    // Only process quick swipes (less than 500ms)
    if (deltaTime > 500) return

    // Only process horizontal swipes (not vertical scrolls)
    if (Math.abs(deltaY) > Math.abs(deltaX)) return

    // Swipe right from left edge to open sidebar
    if (touchStartX.current < 30 && deltaX > 50 && !sidebarOpen) {
      setSidebarOpen(true)
      return
    }

    // Swipe left to close sidebar
    if (sidebarOpen && deltaX < -50) {
      setSidebarOpen(false)
      return
    }
  }

  return (
    <div
      className="flex h-screen overflow-hidden bg-[var(--bg-primary)]"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* Sidebar - overlay on mobile, collapsible on tablet */}
      <div
        className={`
          flex-shrink-0 transition-all duration-300 ease-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          ${isMobile ? 'fixed inset-0 z-40 w-full max-w-[280px]' : ''}
          ${isTablet ? 'fixed inset-y-0 left-0 z-30 w-[260px]' : ''}
        `}
        style={{
          width: sidebarOpen && !isMobile ? sidebarWidth : (isMobile || (isTablet && sidebarOpen)) ? '260px' : 0
        }}
      >
        {/* Backdrop for mobile/tablet overlay */}
        {(isMobile || isTablet) && sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-[-1]"
            onClick={() => setSidebarOpen(false)}
          />
        )}
        <Sidebar />
      </div>

      {/* Main content */}
      <div className="flex flex-1 flex-col min-w-0">
        <Header />
        <main className="flex-1 overflow-hidden">
          <Outlet />
        </main>
      </div>

      {/* Sub-agent indicator - shows when sub-agent is active or extended thinking enabled */}
      <SubAgentIndicator />

      {/* Command Palette - global keyboard shortcut menu */}
      <CommandPalette />

      {/* Onboarding Tour */}
      <OnboardingTour />
    </div>
  )
}
