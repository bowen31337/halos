import { useEffect } from 'react'

export function SkipNavigation() {
  useEffect(() => {
    // Add skip navigation link to the body
    const skipNav = document.createElement('a')
    skipNav.href = '#main-content'
    skipNav.className = 'skip-nav'
    skipNav.textContent = 'Skip to main content'
    skipNav.style.position = 'absolute'
    skipNav.style.left = '-9999px'
    skipNav.style.top = 'auto'
    skipNav.style.width = '1px'
    skipNav.style.height = '1px'
    skipNav.style.overflow = 'hidden'
    skipNav.style.zIndex = '9999'

    document.body.appendChild(skipNav)

    return () => {
      document.body.removeChild(skipNav)
    }
  }, [])

  return null
}