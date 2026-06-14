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

// PROJECT.md (repo root) powers /pm-log via a ?raw import. In docker dev it is
// bind-mounted at /pmsrc/PROJECT.md — the project root can't be nested under the
// ./frontend:/app mount on macOS — and resolves via the @pmlog alias. Bare-metal
// it sits one level above frontend/.
const PM = existsSync("/pmsrc/PROJECT.md")
  ? "/pmsrc/PROJECT.md"
  : fileURLToPath(new URL("../PROJECT.md", import.meta.url))
const PM_DIR = existsSync("/pmsrc/PROJECT.md")
  ? "/pmsrc"
  : fileURLToPath(new URL("..", import.meta.url))

export default defineConfig({
  plugins: [vue()],
  server: {
    host: "0.0.0.0",
    port: 3400,
    fs: { allow: [".", DS, PM_DIR] },
    proxy: {
      "/api":     "http://backend:8000",
      "/healthz": "http://backend:8000",
      "/readyz":  "http://backend:8000",
    },
  },
  resolve: {
    // Array form so @pmlog can use a regex: a string alias only matches
    // `@pmlog` or `@pmlog/...`, NOT `@pmlog?raw`, so the ?raw import needs the
    // regex to match-and-keep the query. Order: most specific first.
    alias: [
      { find: "@ds", replacement: DS },
      { find: /^@pmlog/, replacement: PM },
      { find: "@", replacement: fileURLToPath(new URL("./src", import.meta.url)) },
    ],
  },
})
