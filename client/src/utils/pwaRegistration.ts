/**
 * PWA Registration Utility
 * Handles service worker registration and PWA installation prompts
 */

export interface PWAState {
  isRegistered: boolean
  isInstallable: boolean
  isInstalled: boolean
  deferredPrompt: any | null
  registration: ServiceWorkerRegistration | null
}

let deferredPrompt: any = null
let registration: ServiceWorkerRegistration | null = null

/**
 * Register the service worker
 */
export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (!('serviceWorker' in navigator)) {
    console.log('Service workers are not supported')
    return null
  }

  try {
    const swUrl = '/service-worker.js'
    const reg = await navigator.serviceWorker.register(swUrl)

    console.log('Service worker registered:', reg)
    registration = reg

    // Check for updates
    reg.addEventListener('updatefound', () => {
      const newWorker = reg.installing
      if (newWorker) {
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            console.log('New version available')
            // Could trigger update notification here
          }
        })
      }
    })

    return reg
  } catch (error) {
    console.log('Service worker registration failed:', error)
    return null
  }
}

/**
 * Listen for PWA install prompt
 */
export function setupInstallPrompt(
  onInstallable: (prompt: any) => void,
  onInstalled: () => void
): () => void {
  const beforeInstallPromptHandler = (event: Event) => {
    event.preventDefault()
    deferredPrompt = event
    onInstallable(event)
  }

  const installedHandler = () => {
    onInstalled()
  }

  window.addEventListener('beforeinstallprompt', beforeInstallPromptHandler)
  window.addEventListener('appinstalled', installedHandler)

  return () => {
    window.removeEventListener('beforeinstallprompt', beforeInstallPromptHandler)
    window.removeEventListener('appinstalled', installedHandler)
  }
}

/**
 * Trigger the install prompt
 */
export async function triggerInstallPrompt(): Promise<boolean> {
  if (!deferredPrompt) {
    console.log('Install prompt not available')
    return false
  }

  try {
    deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice

    if (outcome === 'accepted') {
      console.log('User accepted the install prompt')
    } else {
      console.log('User dismissed the install prompt')
    }

    deferredPrompt = null
    return outcome === 'accepted'
  } catch (error) {
    console.log('Error during install prompt:', error)
    return false
  }
}

/**
 * Check if app is already installed
 */
export function isAppInstalled(): boolean {
  // Check if running in standalone mode (PWA)
  const isStandalone = window.matchMedia('(display-mode: standalone)').matches
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent)

  return isStandalone || (isIOS && (window.navigator as any).standalone === true)
}

/**
 * Get PWA state
 */
export function getPWAState(): PWAState {
  return {
    isRegistered: !!registration,
    isInstallable: !!deferredPrompt,
    isInstalled: isAppInstalled(),
    deferredPrompt,
    registration
  }
}

/**
 * Unregister service worker (for cleanup)
 */
export async function unregisterServiceWorker(): Promise<boolean> {
  if (!('serviceWorker' in navigator)) {
    return false
  }

  try {
    const registrations = await navigator.serviceWorker.getRegistrations()
    await Promise.all(registrations.map(reg => reg.unregister()))
    console.log('Service workers unregistered')
    return true
  } catch (error) {
    console.log('Error unregistering service workers:', error)
    return false
  }
}
