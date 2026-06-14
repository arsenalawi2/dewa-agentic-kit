<script setup>
// /pm-log — renders PROJECT.md (at the repo root) as HTML. Edit
// PROJECT.md, this page updates. See ~/.claude/templates/pm-log.md
// for the expected structure.
import { ref, onMounted } from "vue"
import { marked } from "marked"

// Vite's ?raw import ships PROJECT.md (repo root) as a string at build time.
// It resolves via the @pmlog alias (vite.config) — bind-mounted at /pmsrc in
// docker dev since it can't be nested under the /app mount on macOS.
// eslint-disable-next-line import/no-unresolved
import mdSrc from "@pmlog?raw"

// Strip the leading YAML front-matter (--- ... ---) so it doesn't render as
// a stray table, and pull `status` out for the badge.
function splitFrontMatter(src) {
  const m = src.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/)
  if (!m) return { body: src, status: "" }
  let status = ""
  for (const line of m[1].split("\n")) {
    const i = line.indexOf(":")
    if (i > 0 && line.slice(0, i).trim() === "status") {
      status = line.slice(i + 1).split("#")[0].trim().replace(/^["']|["']$/g, "")
    }
  }
  return { body: src.slice(m[0].length), status }
}

const { body, status } = splitFrontMatter(mdSrc)
const html = ref("")
onMounted(async () => {
  // Mermaid is heavy; lazy-load it only if the doc has mermaid blocks.
  html.value = marked.parse(body)
  if (body.includes("```mermaid")) {
    const { default: mermaid } = await import("mermaid")
    mermaid.initialize({ startOnLoad: false })
    await mermaid.run({ querySelector: ".pm-log pre code.language-mermaid" })
  }
})
</script>

<template>
  <div class="page pm-log">
    <header class="head">
      <div class="eyebrow">Project log</div>
      <h1>
        PM log
        <span v-if="status" class="status-badge" :class="`status--${status}`">{{ status }}</span>
      </h1>
    </header>
    <article v-html="html"></article>
  </div>
</template>

<style scoped>
.page { max-width: 760px; }
.head { margin-bottom: 28px; }
.eyebrow {
  font-family: var(--font-display);
  font-size: 11px;
  letter-spacing: 1.4px;
  text-transform: uppercase;
  color: var(--text-accent);
}
h1 {
  font-family: var(--font-display);
  font-size: 32px;
  margin: 6px 0 10px;
}
.status-badge {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 3px 9px;
  border-radius: var(--radius-full, 999px);
  border: 1px solid var(--border-default);
  vertical-align: middle;
  margin-left: 10px;
  color: var(--text-tertiary);
}
.status-badge.status--building { color: var(--color-warning, #b45309); border-color: currentColor; }
.status-badge.status--live { color: var(--color-success, #0f7a3d); border-color: currentColor; }
.status-badge.status--paused { color: var(--text-tertiary); }
.status-badge.status--archived { color: var(--text-tertiary); opacity: 0.6; }
article :deep(h2) {
  font-family: var(--font-display);
  margin-top: 28px;
  margin-bottom: 10px;
}
article :deep(h3) { margin-top: 18px; }
article :deep(p) { line-height: 1.55; opacity: 0.85; }
article :deep(code) {
  font-family: var(--font-mono);
  background: var(--bg-secondary);
  padding: 2px 5px;
  border-radius: 4px;
  font-size: 12px;
}
article :deep(pre) {
  background: var(--bg-secondary);
  padding: 14px;
  border-radius: 8px;
  overflow-x: auto;
}
</style>
