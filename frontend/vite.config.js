import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
      "/auth": "http://localhost:8000",
      "/resume": "http://localhost:8000",
      "/analyze": "http://localhost:8000",
      "/analysis-results": "http://localhost:8000",
      "/jobs": "http://localhost:8000",
      "/applications": "http://localhost:8000",
      "/favorites": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
});