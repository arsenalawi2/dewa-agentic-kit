<script setup>
// /architecture — reads public/tech-stack.json. The DAK hook (push_stats.py)
// auto-detects the stack from package.json / requirements.txt / docker-
// compose.yml and writes the canonical v2 shape: { categories, projects:[
// { name, purpose, stack: { category: [items] } } ] }. Hand-edit the JSON to
// add things the hook can't detect (Tailscale, external APIs) — the hook
// preserves hand-curated entries.
import { ref, onMounted, computed } from "vue"

const data = ref(null)
const error = ref(null)

onMounted(async () => {
  try {
    const res = await fetch("/tech-stack.json")
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    data.value = await res.json()
  } catch (e) {
    error.value = e.message
  }
})

const projects = computed(() => data.value?.projects || [])
const categories = computed(() => data.value?.categories || {})
const legacyGroups = computed(() => data.value?.groups || [])

function label(cat) {
  return categories.value[cat]?.label || cat
}
function stackEntries(stack) {
  return Object.entries(stack || {}).filter(([, items]) => items && items.length)
}
</script>

<template>
  <div class="page">
    <header class="head">
      <div class="eyebrow">Under the hood</div>
      <h1>Architecture</h1>
    </header>

    <div v-if="error" class="state error">Couldn't load: {{ error }}</div>
    <div v-else-if="!data" class="state">Loading stack…</div>

    <!-- Canonical v2 schema -->
    <div v-else-if="projects.length" class="projects">
      <section v-for="p in projects" :key="p.id || p.name" class="project">
        <h2>{{ p.name }}</h2>
        <p v-if="p.purpose" class="purpose">{{ p.purpose }}</p>
        <div class="cats">
          <div v-for="[cat, items] in stackEntries(p.stack)" :key="cat" class="cat">
            <span class="cat-label" :style="{ color: categories[cat]?.color }">{{ label(cat) }}</span>
            <ul>
              <li v-for="t in items" :key="t" class="chip">{{ t }}</li>
            </ul>
          </div>
        </div>
      </section>
    </div>

    <!-- Legacy {groups} fallback so older files still render -->
    <div v-else-if="legacyGroups.length" class="groups">
      <section v-for="g in legacyGroups" :key="g.label" class="group">
        <h2>{{ g.label }}</h2>
        <ul>
          <li v-for="t in g.items" :key="t.name">
            <span class="tech-name">{{ t.name }}</span>
            <span v-if="t.version" class="tech-version">{{ t.version }}</span>
            <span v-if="t.note" class="tech-note">— {{ t.note }}</span>
          </li>
        </ul>
      </section>
    </div>

    <div v-else class="state">No stack data yet.</div>
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
.state { padding: 40px; text-align: center; opacity: 0.7; }
.state.error { color: #c44; }

/* v2 schema */
.projects { display: flex; flex-direction: column; gap: 32px; }
.project h2 { font-family: var(--font-display); font-size: 20px; margin: 0 0 4px; }
.purpose { margin: 0 0 14px; opacity: 0.75; }
.cats { display: flex; flex-direction: column; gap: 16px; }
.cat-label {
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.6px;
}
.cat ul {
  list-style: none;
  padding: 0;
  margin: 8px 0 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.chip {
  font-size: 13px;
  padding: 4px 10px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-full, 999px);
  background: var(--bg-secondary);
}

/* legacy {groups} */
.groups { display: flex; flex-direction: column; gap: 24px; }
.group h2 {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  margin: 0 0 10px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: var(--text-tertiary);
}
.group ul { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 4px; }
.tech-name { font-weight: 600; }
.tech-version {
  margin-left: 8px;
  font-family: var(--font-mono);
  font-size: 12px;
  opacity: 0.7;
}
.tech-note { margin-left: 8px; opacity: 0.7; }
</style>
