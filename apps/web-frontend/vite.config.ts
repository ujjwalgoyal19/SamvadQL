/// <reference types="vitest" />
import { defineConfig } from 'vite';
import { fileURLToPath, URL } from 'node:url';
import tailwindcss from '@tailwindcss/vite';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    hmr: {
      port: 24678,
      protocol: 'ws',
      clientPort: 24678
    },
    watch: {
      usePolling: true,
      interval: 1000
    }
  },
  preview: {
    host: '0.0.0.0',
    port: 3000
  }
});
