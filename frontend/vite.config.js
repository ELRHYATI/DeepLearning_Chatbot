import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom']
        }
      }
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        timeout: 60000, // 60 secondes
        ws: true, // Enable WebSocket proxying
        configure: (proxy, _options) => {
          proxy.on('error', (err, req, res) => {
            // Handle connection errors gracefully
            if (err.code === 'ECONNRESET' || err.code === 'ECONNREFUSED') {
              console.warn(`Proxy connection error (${err.code}):`, req.url);
              // Don't crash, just log the error
              if (!res.headersSent) {
                res.writeHead(502, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({
                  error: true,
                  message: 'Backend server connection error. Please ensure the backend is running on port 8000.',
                  code: err.code
                }));
              }
            } else {
              console.error('Proxy error:', err);
            }
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Proxying request:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            // Log successful responses for debugging
            if (proxyRes.statusCode >= 500) {
              console.warn(`Backend error ${proxyRes.statusCode} for:`, req.url);
            }
          });
        }
      }
    }
  },
  publicDir: 'public'
})
