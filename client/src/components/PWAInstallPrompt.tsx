import { useState, useEffect } from 'react'
import { setupInstallPrompt, triggerInstallPrompt, isAppInstalled } from '../utils/pwaRegistration'

/**
 * PWAInstallPrompt - Shows a banner when the app can be installed
 */
export function PWAInstallPrompt() {
  const [showPrompt, setShowPrompt] = useState(false)
  const [isInstalling, setIsInstalling] = useState(false)
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    // Don't show if already installed or dismissed
    if (isAppInstalled() || dismissed) {
      return
    }

    // Check if we're in standalone mode
    if (window.matchMedia('(display-mode: standalone)').matches) {
      return
    }

    const cleanup = setupInstallPrompt(
      () => {
        // App is installable
        setShowPrompt(true)
      },
      () => {
        // App was installed
        setShowPrompt(false)
      }
    )

    return cleanup
  }, [dismissed])

  const handleInstall = async () => {
    setIsInstalling(true)
    const success = await triggerInstallPrompt()
    setIsInstalling(false)

    if (success) {
      setShowPrompt(false)
    }
  }

  const handleDismiss = () => {
    setDismissed(true)
    setShowPrompt(false)
  }

  if (!showPrompt) return null

  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 z-[9998]">
      <div className="bg-[var(--surface-elevated)] border border-[var(--border-primary)] rounded-lg shadow-xl p-4">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0">
            <svg className="w-6 h-6 text-[var(--primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-1">
              Install Claude AI Clone
            </h3>
            <p className="text-xs text-[var(--text-secondary)] mb-3">
              Install the app for a better experience with offline access and notifications
            </p>
            <div className="flex gap-2">
              <button
                onClick={handleInstall}
                disabled={isInstalling}
                className="px-3 py-1.5 bg-[var(--primary)] text-white rounded text-xs font-medium hover:bg-[var(--primary-hover)] transition-colors disabled:opacity-50"
              >
                {isInstalling ? 'Installing...' : 'Install'}
              </button>
              <button
                onClick={handleDismiss}
                className="px-3 py-1.5 bg-[var(--surface-secondary)] text-[var(--text-primary)] rounded text-xs font-medium hover:bg-[var(--surface-elevated)] transition-colors"
              >
                Maybe later
              </button>
            </div>
          </div>
          <button
            onClick={handleDismiss}
            className="flex-shrink-0 p-1 text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            aria-label="Close"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}

/**
 * PWAStatusIndicator - Shows PWA installation status in settings
 */
export function PWAStatusIndicator() {
  const [isInstalled, setIsInstalled] = useState(false)
  const [isInstallable, setIsInstallable] = useState(false)

  useEffect(() => {
    const checkStatus = () => {
      setIsInstalled(isAppInstalled())
      // Check if install prompt would work
      setIsInstallable(
        window.matchMedia('(display-mode: standalone)').matches === false &&
        'beforeinstallprompt' in window
      )
    }

    checkStatus()

    const interval = setInterval(checkStatus, 1000)
    return () => clearInterval(interval)
  }, [])

  if (isInstalled) {
    return (
      <div className="flex items-center gap-2 text-[var(--status-success)] text-sm">
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
        Installed as PWA
      </div>
    )
  }

  if (isInstallable) {
    return (
      <div className="flex items-center gap-2 text-[var(--text-secondary)] text-sm">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        Installable - Available in browser menu
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2 text-[var(--text-secondary)] text-sm">
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      Not installable in this browser
    </div>
  )
}
