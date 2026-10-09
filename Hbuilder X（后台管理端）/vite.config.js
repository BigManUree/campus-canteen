import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

const backendTarget = 'http://localhost:8000'
const workspaceRoot = fileURLToPath(new URL('.', import.meta.url))
const dayjsEsmPath = fileURLToPath(new URL('./node_modules/dayjs/esm/index.js', import.meta.url))
const dayjsPluginDir = fileURLToPath(new URL('./node_modules/dayjs/esm/plugin', import.meta.url))

export default defineConfig({
  root: workspaceRoot,
  plugins: [vue()],
  resolve: {
    alias: [
      {
        find: /^dayjs\/plugin\/(.+)\.js$/,
        replacement: `${dayjsPluginDir}/$1/index.js`
      },
      {
        find: 'dayjs',
        replacement: dayjsEsmPath
      },
      {
        find: '@',
        replacement: fileURLToPath(new URL('./src', import.meta.url))
      }
    ]
  },
  optimizeDeps: {
    noDiscovery: true,
    include: []
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    fs: {
      allow: [workspaceRoot]
    },
    watch: {
      ignored: ['**/node_modules/**', '**/.git/**', '**/dist/**']
    },
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true
      },
      '/uploads': {
        target: backendTarget,
        changeOrigin: true
      }
    }
  }
})

