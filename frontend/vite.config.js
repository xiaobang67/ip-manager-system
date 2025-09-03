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
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    rollupOptions: {
      output: {
        // 添加时间戳到文件名，强制缓存失效
        entryFileNames: (chunkInfo) => {
          const timestamp = Date.now();
          return `assets/[name]-[hash]-${timestamp}.js`;
        },
        chunkFileNames: (chunkInfo) => {
          const timestamp = Date.now();
          return `assets/[name]-[hash]-${timestamp}.js`;
        },
        assetFileNames: (assetInfo) => {
          const timestamp = Date.now();
          return `assets/[name]-[hash]-${timestamp}.[ext]`;
        }
      }
    }
  }
})