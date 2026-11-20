import tailwindcss from "@tailwindcss/vite";
import { tanstackRouter } from "@tanstack/router-plugin/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Django serves the build from /static/ (frontend/dist is in STATICFILES_DIRS) and
// django-vite reads dist/manifest.json. In dev, django-vite points at this server.
export default defineConfig({
  base: "/static/",
  plugins: [
    // Must come before react() so it can code-split route files.
    tanstackRouter({ target: "react", autoCodeSplitting: true }),
    react(),
    tailwindcss(),
  ],
  server: {
    port: 5173,
    strictPort: true,
    origin: "http://localhost:5173",
    cors: { origin: ["http://localhost:8000", "http://127.0.0.1:8000"] },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    manifest: "manifest.json",
    rollupOptions: { input: "src/main.tsx" },
  },
});
