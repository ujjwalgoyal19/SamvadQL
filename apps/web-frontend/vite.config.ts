import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    host: "0.0.0.0",
    port: 3000,
    hmr: {
      port: 24678,
      protocol: "ws",
      clientPort: 24678,
    },
    watch: {
      usePolling: true,
      interval: 100,
    },
  },
  preview: {
    host: "0.0.0.0",
    port: 3000,
  },
});
