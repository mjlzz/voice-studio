import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 2345,
    proxy: {
      '/api': {
        target: 'http://localhost:8765',
        changeOrigin: true
      }
    }
  }
})