<script setup>
// DAK project shell — hover-expand rail (a 64px icon rail that expands to
// 240px on hover/focus) with SVG nav icons from the design system. The four
// auto-pages stay wired; add your own routes to NAV as the app grows.
import { ref } from "vue"
import Icon from "@ds/components/Icon.vue"

const dark = ref(false)
function toggleTheme() {
  dark.value = !dark.value
  document.documentElement.classList.toggle("dark", dark.value)
}

const NAV = [
  { to: "/",             icon: "home",      label: "Home" },
  { to: "/journey",      icon: "flag",      label: "Journey" },
  { to: "/architecture", icon: "layers",    label: "Architecture" },
  { to: "/vibe-code",    icon: "code",      label: "Vibe code" },
  { to: "/pm-log",       icon: "clipboard", label: "PM log" },
]
</script>

<template>
  <div class="app-shell app-shell--rail">
    <aside class="sidebar">
      <div class="sidebar-top">
        <div class="brand">
          <span class="rail-icon"><Icon name="spark" /></span>
          <span class="rail-label">{{ "{{PROJECT_NAME}}" }}</span>
        </div>
      </div>
      <div class="sidebar-scroll">
        <ul class="list">
          <li v-for="n in NAV" :key="n.to">
            <RouterLink :to="n.to" class="list-row nav-row" active-class="is-active">
              <span class="rail-icon"><Icon :name="n.icon" /></span>
              <span class="rail-label">{{ n.label }}</span>
            </RouterLink>
          </li>
        </ul>
      </div>
      <div class="sidebar-footer">
        <button class="btn btn-ghost btn-sm btn-block" @click="toggleTheme">
          <span class="rail-icon"><Icon :name="dark ? 'sun' : 'moon'" /></span>
          <span class="rail-label">{{ dark ? "Light" : "Dark" }} mode</span>
        </button>
      </div>
    </aside>
    <main class="main" id="main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
/* RouterLink renders an <a>; keep the design system's row look + colors. */
.nav-row { color: var(--color-text); text-decoration: none; }
.nav-row:hover { text-decoration: none; }
</style>
