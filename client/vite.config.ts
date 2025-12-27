import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { esbuild } from 'esbuild'

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
  optimizeDeps: {
    esbuildOptions: {
      // Use the Node.js esbuild binary instead of native
      platform: 'node',
    },
  },
})
