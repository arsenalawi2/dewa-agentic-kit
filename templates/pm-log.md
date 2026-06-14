# PM Log Page Template

Create a `/pm-log` route that renders the project's `PROJECT.md` file as a browsable, styled project management log — including the Mermaid Gantt chart in §4.2.

## Data Source

**Primary (no JSON intermediate):** The root `PROJECT.md` is imported directly into the Vue component at build time using Vite's `?raw` suffix. There is no separate data file and no hook. Whatever Claude Code writes to `PROJECT.md` is what this page displays.

```javascript
import pmLogRaw from '@/../../PROJECT.md?raw'
```

The exact relative path depends on where the Vue component lives. For a standard Vue 3 + Vite layout (`frontend/src/views/PmLog.vue`) and `PROJECT.md` at the repo root, the path is `../../../PROJECT.md?raw`. Adjust if the component lives elsewhere.

**Why build-time import and not a runtime fetch?** `PROJECT.md` lives at the repo root, not in `public/`. Vite's `?raw` import lets us read it directly without copying the file or adding a backend endpoint. Vite's HMR picks up changes to `PROJECT.md` automatically in dev, and production rebuilds happen naturally as part of the existing Docker/deploy flow.

## Dependencies

Install these in the frontend:

```bash
npm install marked mermaid
```

- `marked` — markdown → HTML renderer (tiny, fast, well-maintained)
- `mermaid` — renders the Gantt chart and any other diagrams embedded in `PROJECT.md`

## Page Structure

Sidebar-first layout per the EZ Design System:

```
+--sidebar 260px------+------- main content -------+
| Brand               | Header: project name,      |
| Table of Contents   |   last updated, status     |
|   01 Charter        |                            |
|   02 Scope          | Rendered markdown:         |
|   03 WBS            |   §1 Charter               |
|   04 Schedule       |   §2 Scope                 |
|   05 Deliverables   |   §3 WBS                   |
|   06 Cost           |   §4 Schedule (Gantt)      |
|   07 Risks          |   §5 Deliverables          |
|   08 Issues         |   §6 Cost                  |
|   09 Changes        |   §7 Risks                 |
|   10 Lessons        |   …                        |
|   11 Status         |                            |
| ─────────────────   |                            |
| Theme toggle        |                            |
+---------------------+----------------------------+
```

### Sidebar — Table of Contents

- Parse the 11 top-level `## N. Title` headings out of the markdown and build a nav from them.
- Each link scrolls smoothly to its section (`scrollIntoView({ behavior: 'smooth' })`).
- Highlight the currently-visible section using an IntersectionObserver.
- Collapse under 960px.

### Main content

- Max width ~900px for long-form readability.
- Render the markdown via `marked.parse()` and drop into a `v-html` container.
- Tables inherit EZ Design System styling (warm neutrals, subtle borders, hover row shift).
- Mermaid fenced blocks are picked up by a custom renderer (see below) and initialized with `mermaid.run()` after mount.

## Core Vue Component

```vue
<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { marked } from 'marked'
import mermaid from 'mermaid'
import pmLogRaw from '../../../PROJECT.md?raw'

const contentEl = ref(null)
const activeSection = ref('')
const isDark = ref(document.documentElement.classList.contains('dark'))

// Custom renderer: pass through Mermaid fenced blocks as <div class="mermaid">
marked.use({
  renderer: {
    code(code, infostring) {
      const lang = (infostring || '').trim().split(/\s+/)[0]
      if (lang === 'mermaid') return `<div class="mermaid">${code}</div>`
      const escaped = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      return `<pre><code class="lang-${lang}">${escaped}</code></pre>`
    },
    heading(text, level) {
      const id = text.toLowerCase().replace(/[^\w\s-]/g, '').replace(/\s+/g, '-')
      return `<h${level} id="${id}">${text}</h${level}>`
    }
  }
})

// Parse the 11 top-level sections from the raw markdown for the sidebar
const sections = computed(() => {
  const matches = [...pmLogRaw.matchAll(/^## (\d+)\.\s+(.+)$/gm)]
  return matches.map(m => ({
    num: m[1].padStart(2, '0'),
    title: m[2].trim(),
    id: m[2].toLowerCase().replace(/[^\w\s-]/g, '').replace(/\s+/g, '-')
  }))
})

// Parse the header metadata table (Project Name, Status, Last Updated)
const meta = computed(() => {
  const rows = pmLogRaw.match(/\| \*\*([^*]+)\*\* \| ([^|]+) \|/g) || []
  const obj = {}
  rows.forEach(row => {
    const m = row.match(/\| \*\*([^*]+)\*\* \| ([^|]+) \|/)
    if (m) obj[m[1].trim()] = m[2].trim().replace(/^_|_$/g, '')
  })
  return obj
})

const html = computed(() => marked.parse(pmLogRaw))

function scrollToSection(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

let observer = null
onMounted(async () => {
  await nextTick()

  // Initialize Mermaid with current theme
  mermaid.initialize({
    startOnLoad: false,
    theme: isDark.value ? 'dark' : 'default',
    gantt: { barHeight: 24, barGap: 6, fontSize: 12, sectionFontSize: 13 }
  })
  await mermaid.run({ nodes: contentEl.value.querySelectorAll('.mermaid') })

  // Highlight section on scroll
  observer = new IntersectionObserver(
    entries => {
      entries.forEach(e => {
        if (e.isIntersecting) activeSection.value = e.target.id
      })
    },
    { rootMargin: '-30% 0px -60% 0px' }
  )
  contentEl.value.querySelectorAll('h2[id]').forEach(h => observer.observe(h))
})

onUnmounted(() => observer?.disconnect())
</script>

<template>
  <div class="pm-layout">
    <aside class="pm-sidebar">
      <div class="pm-brand">
        <div class="pm-brand-mark">{{ meta['Project Name'] || 'Project Log' }}</div>
        <div class="pm-brand-sub">PMBOK 7 · {{ meta['Status'] || '—' }}</div>
      </div>
      <nav class="pm-toc">
        <div class="pm-toc-title">Contents</div>
        <a
          v-for="s in sections"
          :key="s.id"
          :class="{ active: activeSection === s.id }"
          @click.prevent="scrollToSection(s.id)"
          :href="'#' + s.id"
        >
          <span class="pm-toc-num">{{ s.num }}</span>
          <span>{{ s.title }}</span>
        </a>
      </nav>
      <div class="pm-meta">
        <div class="pm-meta-row"><span>Updated</span><b>{{ meta['Last Updated'] || '—' }}</b></div>
        <div class="pm-meta-row"><span>PM</span><b>{{ meta['Project Manager'] || '—' }}</b></div>
      </div>
    </aside>
    <main class="pm-main">
      <div ref="contentEl" class="pm-content" v-html="html"></div>
    </main>
  </div>
</template>
```

## Styling Notes

Use EZ Design System tokens. Key rules:

- **Content typography** — `font-family: var(--font-sans)` for body; headings inherit `var(--font-display)`. Base size 15px, line-height 1.65, max-width 860px.
- **Headings** — `h2` (section titles) at 28px with 56px top margin and a 1px bottom border. `h3` (sub-sections) at 18px with 36px top margin.
- **Tables** — `border-collapse: collapse`, header row uses `var(--bg-secondary)` with uppercase 11px display-font labels, rows have `var(--border-light)` bottom borders, row hover uses `var(--bg-hover)`.
- **Code blocks** — `var(--bg-secondary)` background, `var(--font-mono)` at 12px, 12px padding, 8px radius.
- **Inline code** — same font, `var(--bg-tertiary)` background, 2px/6px padding, 4px radius.
- **Mermaid block** — full width up to the container, `var(--bg-secondary)` background, 1px `var(--border-light)` border, 20px padding, 12px radius, horizontal scroll on overflow.
- **Sidebar** — 260px wide, sticky, full height. Brand block on top, ToC in the middle, metadata at the bottom. ToC links: 13px display font, `var(--text-secondary)`, hover → `var(--text-primary)`, active → `var(--text-accent)` with `var(--bg-accent)` background and 3px left border in accent green.
- **Status labels** — detect `[Pending]`, `[In Progress]`, `[Complete]`, `[Deferred]`, `[Blocked]`, `[Mitigated]`, `[Resolved]`, `[Open]` etc. in the rendered HTML and wrap them in styled spans. Simple approach: post-process the `html` string with a regex replacement before assigning it to `v-html`. The pill uses `var(--bg-accent)` for complete/mitigated, warm amber for in-progress, muted gray for pending/deferred.

```javascript
// Status label styling — run after marked.parse
const statusColors = {
  Complete: 'var(--color-success)',
  Resolved: 'var(--color-success)',
  Mitigated: 'var(--color-success)',
  Delivered: 'var(--color-success)',
  Active: 'var(--color-warning)',
  'In Progress': 'var(--color-warning)',
  Open: 'var(--color-warning)',
  Monitoring: 'var(--color-warning)',
  Pending: 'var(--text-muted)',
  Deferred: 'var(--text-muted)',
  Future: 'var(--text-muted)',
  Blocked: 'var(--color-error)',
  Critical: 'var(--color-error)',
  High: 'var(--color-error)',
  Medium: 'var(--color-warning)',
  Low: 'var(--text-muted)'
}

function decorate(html) {
  return html.replace(/\[(Complete|Resolved|Mitigated|Delivered|Active|In Progress|Open|Monitoring|Pending|Deferred|Future|Blocked|Critical|High|Medium|Low|Done)\]/g,
    (_, label) => `<span class="pm-status" style="--c:${statusColors[label] || 'var(--text-muted)'}">${label}</span>`
  )
}

// Use `decorate(marked.parse(pmLogRaw))` in the computed
```

## Dark Mode

Mermaid needs to re-render when the theme toggles. Watch the `dark` class on `document.documentElement` via a MutationObserver, then call `mermaid.initialize({ theme: 'dark' | 'default' })` and re-run on the existing `.mermaid` nodes. The surrounding page styling is handled by the EZ Design System tokens automatically.

## Content Guidelines

- **This page renders, it does not author.** The content is whatever is in `PROJECT.md`. Edit the markdown, not the Vue component.
- **Single source of truth.** Never fork the PM log into a separate JSON file or a hardcoded Vue template. That defeats the point of option 1.
- **Gantt first-class.** The Mermaid Gantt in §4.2 is a core PMBOK artifact; make sure it renders correctly in both light and dark mode. If Mermaid fails to parse, fall back gracefully to showing the raw code block (don't crash the page).
- **Cross-link to `/journey` and `/vibe-code`.** The PM log is analytical; the journey page is narrative; the vibe-code page is usage stats. All three together tell the full story of the project.

## Page Purpose

The PM log is the project's formal management artifact — stakeholders, auditors, and new team members read it to understand where the project is, what decisions have been made, what risks are tracked, and what's next. Unlike the journey page (narrative showcase) or the vibe-code page (usage stats), this page is structured, dense, and PMI-compliant. Treat it like you would treat a Jira + Confluence combo — the single source of truth for project execution.
