import { useState, useEffect, useRef, useCallback, ReactNode } from 'react'
import { create } from 'zustand'

export interface ContextMenuItem {
  id: string
  label: string
  icon?: ReactNode
  onClick?: () => void
  shortcut?: string
  disabled?: boolean
  danger?: boolean
}

interface ContextMenuState {
  isOpen: boolean
  x: number
  y: number
  items: ContextMenuItem[]
  targetElement: HTMLElement | null
}

interface ContextMenuStore extends ContextMenuState {
  open: (x: number, y: number, items: ContextMenuItem[], targetElement: HTMLElement | null) => void
  close: () => void
}

// Context menu store using Zustand
export const useContextMenuStore = create<ContextMenuStore>((set) => ({
  isOpen: false,
  x: 0,
  y: 0,
  items: [],
  targetElement: null,
  open: (x, y, items, targetElement) => set({ isOpen: true, x, y, items, targetElement }),
  close: () => set({ isOpen: false, items: [], targetElement: null }),
}))

// Context menu component
export function ContextMenu() {
  const { isOpen, x, y, items, close } = useContextMenuStore()
  const menuRef = useRef<HTMLDivElement>(null)
  const [position, setPosition] = useState({ x, y })

  // Handle click outside
  useEffect(() => {
    if (!isOpen) return

    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        close()
      }
    }

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        close()
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen, close])

  // Adjust position to stay within viewport
  useEffect(() => {
    if (!isOpen) return

    const adjustPosition = () => {
      if (!menuRef.current) return

      const rect = menuRef.current.getBoundingClientRect()
      let newX = x
      let newY = y

      // Adjust if menu goes off right edge
      if (rect.right > window.innerWidth) {
        newX = x - rect.width
      }

      // Adjust if menu goes off bottom edge
      if (rect.bottom > window.innerHeight) {
        newY = y - rect.height
      }

      // Ensure minimum distance from edges
      newX = Math.max(8, Math.min(newX, window.innerWidth - rect.width - 8))
      newY = Math.max(8, Math.min(newY, window.innerHeight - rect.height - 8))

      setPosition({ x: newX, y: newY })
    }

    // Small delay to allow menu to render
    setTimeout(adjustPosition, 10)
  }, [isOpen, x, y])

  if (!isOpen) return null

  return (
    <>
      <div className="context-menu-backdrop" onClick={close} />
      <div
        ref={menuRef}
        className="context-menu"
        style={{
          left: `${position.x}px`,
          top: `${position.y}px`,
        }}
        role="menu"
        aria-label="Context menu"
      >
        {items.map((item, index) => (
          <div key={item.id}>
            {index > 0 && <div className="context-menu-divider" />}
            <div
              className={`context-menu-item ${item.danger ? 'danger' : ''} ${item.disabled ? 'disabled' : ''}`}
              onClick={() => {
                if (!item.disabled && item.onClick) {
                  item.onClick()
                  close()
                }
              }}
              role="menuitem"
              aria-disabled={item.disabled}
            >
              {item.icon && <span className="icon">{item.icon}</span>}
              <span>{item.label}</span>
              {item.shortcut && <span className="context-menu-shortcut">{item.shortcut}</span>}
            </div>
          </div>
        ))}
      </div>
    </>
  )
}

// Hook for context menu
export function useContextMenu() {
  const open = useContextMenuStore((state) => state.open)
  const close = useContextMenuStore((state) => state.close)

  const openContextMenu = useCallback(
    (event: React.MouseEvent, items: ContextMenuItem[]) => {
      event.preventDefault()
      event.stopPropagation()
      open(event.clientX, event.clientY, items, event.currentTarget as HTMLElement)
    },
    [open]
  )

  return { openContextMenu, closeContextMenu: close }
}

// Helper to create standard conversation context menu items
export const createConversationMenuItems = (
  onRename: () => void,
  onArchive: () => void,
  onDelete: () => void,
  onShare: () => void
): ContextMenuItem[] => [
  {
    id: 'share',
    label: 'Share',
    icon: (
      <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
      </svg>
    ),
    onClick: onShare,
  },
  {
    id: 'rename',
    label: 'Rename',
    icon: (
      <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
      </svg>
    ),
    onClick: onRename,
  },
  {
    id: 'archive',
    label: 'Archive',
    icon: (
      <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
      </svg>
    ),
    onClick: onArchive,
  },
  {
    id: 'delete',
    label: 'Delete',
    icon: (
      <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
      </svg>
    ),
    onClick: onDelete,
    danger: true,
  },
]
