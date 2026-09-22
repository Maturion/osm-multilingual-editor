import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    strictPort: true,
    allowedHosts: ['frontend', 'localhost'],
    // Vite runs on :5173 inside the container, but the browser talks to it
    // through the Caddy proxy on https://localhost:443 - tell the HMR client
    // to reconnect there instead of guessing from its own port.
    hmr: {
      protocol: 'wss',
      host: 'localhost',
      clientPort: 443,
    },
  },
})
