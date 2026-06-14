import { existsSync } from "node:fs"
import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"
import { fileURLToPath, URL } from "node:url"

// The DAK design system resolves from /ds when bind-mounted (the docker dev
// service mounts ~/design-system there) and falls back to ~/design-system for
// bare-metal dev when the project sits two levels under $HOME (e.g. ~/code/<p>).
const DS = existsSync("/ds/index.css")
  ? "/ds"
  : fileURLToPath(new URL("../../../design-system", import.meta.url))

export default defineConfig({
  plugins: [vue()],
  server: {
    host: "0.0.0.0",
    port: 3400,
    fs: { allow: [".", DS] },
    proxy: {
      "/api":     "http://backend:8000",
      "/healthz": "http://backend:8000",
      "/readyz":  "http://backend:8000",
    },
  },
  resolve: {
    alias: {
      "@":  fileURLToPath(new URL("./src", import.meta.url)),
      "@ds": DS,
    },
  },
})
