import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // Enable code splitting
    rollupOptions: {
      output: {
        manualChunks: {
          // Split vendor dependencies
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'state-vendor': ['zustand', '@tanstack/react-query'],
          'ui-vendor': ['react-window', 'react-syntax-highlighter', 'react-markdown'],
          'utils-vendor': ['uuid', 'remark-gfm'],
          // Split heavy components
          'settings-components': ['./src/components/SettingsModal.tsx'],
          'message-components': ['./src/components/MessageBubble.tsx', './src/components/MessageList.tsx'],
          'panel-components': ['./src/components/ArtifactPanel.tsx', './src/components/TodoPanel.tsx'],
        },
      },
    },
    // Optimize chunk size
    chunkSizeWarningLimit: 500,
  },
  optimizeDeps: {
    esbuildOptions: {
      platform: 'node',
    },
  },
})
