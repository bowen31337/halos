import { useState, useEffect, useRef } from 'react'

interface OptimizedImageProps {
  src: string
  alt: string
  className?: string
  placeholderClassName?: string
  // If the backend supports thumbnail generation, pass the thumbnail URL
  thumbnailSrc?: string
  // Maximum size for thumbnail (in KB)
  maxThumbnailSize?: number
}

/**
 * OptimizedImage - A smart image component that:
 * 1. Loads a low-res placeholder/thumbnail first
 * 2. Lazy loads the full image when in viewport
 * 3. Shows a loading state while loading
 * 4. Handles errors gracefully
 */
export function OptimizedImage({
  src,
  alt,
  className = '',
  placeholderClassName = '',
  thumbnailSrc,
  maxThumbnailSize = 50,
}: OptimizedImageProps) {
  const [isLoaded, setIsLoaded] = useState(false)
  const [hasError, setHasError] = useState(false)
  const [showFull, setShowFull] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const [isVisible, setIsVisible] = useState(false)

  // Intersection Observer for lazy loading
  useEffect(() => {
    if (!containerRef.current) return

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible(true)
            observer.disconnect()
          }
        })
      },
      {
        rootMargin: '100px', // Start loading slightly before entering viewport
        threshold: 0.01,
      }
    )

    observer.observe(containerRef.current)
    return () => observer.disconnect()
  }, [])

  // Check if we should use thumbnail
  const shouldUseThumbnail = thumbnailSrc && !showFull

  // Handle image load
  const handleLoad = () => {
    setIsLoaded(true)
    // After thumbnail loads, delay full image load for better UX
    if (shouldUseThumbnail && !showFull) {
      setTimeout(() => setShowFull(true), 300)
    }
  }

  // Handle error
  const handleError = () => {
    setHasError(true)
    setIsLoaded(true)
  }

  if (hasError) {
    return (
      <div className={`flex items-center justify-center bg-[var(--surface-secondary)] border border-[var(--border-primary)] rounded-lg ${className}`}>
        <div className="text-center p-4">
          <svg className="w-8 h-8 mx-auto mb-2 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <p className="text-xs text-[var(--text-secondary)]">Image unavailable</p>
        </div>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className={`relative overflow-hidden ${className}`}
    >
      {/* Loading placeholder - shows until image loads */}
      {!isLoaded && (
        <div className={`absolute inset-0 bg-[var(--surface-secondary)] animate-pulse ${placeholderClassName}`}>
          <div className="flex items-center justify-center h-full">
            <svg className="w-8 h-8 text-[var(--border-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        </div>
      )}

      {/* Thumbnail (if available) */}
      {shouldUseThumbnail && isVisible && (
        <img
          src={thumbnailSrc}
          alt={alt}
          className={`w-full h-full object-contain ${isLoaded ? 'opacity-100' : 'opacity-0'} transition-opacity duration-300`}
          onLoad={handleLoad}
          onError={handleError}
          loading="lazy"
        />
      )}

      {/* Full image - lazy loaded */}
      {isVisible && (!shouldUseThumbnail || showFull) && (
        <img
          src={src}
          alt={alt}
          className={`w-full h-full object-contain transition-opacity duration-500 ${isLoaded ? 'opacity-100' : 'opacity-0'}`}
          onLoad={handleLoad}
          onError={handleError}
          loading="lazy"
        />
      )}

      {/* Loading indicator overlay */}
      {isVisible && !isLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-[var(--surface-secondary)]/50">
          <div className="loading-spinner"></div>
        </div>
      )}

      {/* Zoom indicator for large images */}
      {isLoaded && !shouldUseThumbnail && (
        <div className="absolute bottom-2 right-2 bg-black/50 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity">
          Click to expand
        </div>
      )}
    </div>
  )
}
