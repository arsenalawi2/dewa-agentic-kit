<script setup>
// <Icon name="home" /> — the design system's line-icon set.
//
// Dependency-free Vue adjunct (like Aed.vue / Sparkline.vue): one inline
// <svg> per icon, every glyph authored as pure <path> data on a 24×24 grid.
// Stroke = currentColor at 1.5, so icons inherit text color and follow
// hover/active/dark states automatically — drop one into a .rail-icon and
// it just works. Size via the `size` prop (px) or by setting font-size /
// width on a wrapper.
//
// This replaces the Unicode geometric glyphs (◆ ◈ ▤ …) people were using as
// nav icons — those render inconsistently across fonts and look "off".
//
// Add an icon: append a name → array-of-path-strings entry to ICONS below.
// Keep every path on the 24×24 box, stroke-based (no fills).
import { computed } from "vue"

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 20 },
})

const ICONS = {
  // — DAK auto-page nav —
  home:        ["M3 10.6 12 3l9 7.6", "M5.5 9.3V20h13V9.3", "M9.5 20v-5.5h5V20"],
  flag:        ["M5 21V4", "M5 4h11l-2.2 3.2L16 10.5H5"],            // journey / milestones
  layers:      ["M12 2.5 2.5 7 12 11.5 21.5 7 12 2.5Z", "M2.5 12 12 16.5 21.5 12", "M2.5 16.8 12 21.3 21.5 16.8"], // architecture
  code:        ["M9 8.5 5 12l4 3.5", "M15 8.5 19 12l-4 3.5", "M13.5 6.5 10.5 17.5"], // vibe code
  clipboard:   ["M9 4.5H7a2 2 0 0 0-2 2V20a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V6.5a2 2 0 0 0-2-2h-2",
                "M9 3.8a1.2 1.2 0 0 1 1.2-1.2h3.6A1.2 1.2 0 0 1 15 3.8v1.4a1.2 1.2 0 0 1-1.2 1.2h-3.6A1.2 1.2 0 0 1 9 5.2Z",
                "M9 12h6", "M9 16h6"], // pm log

  // — general nav / actions —
  dashboard:   ["M4 4h6v6H4Z", "M14 4h6v6h-6Z", "M14 14h6v6h-6Z", "M4 14h6v6H4Z"],
  chart:       ["M4 4v16h16", "M8 16v-4", "M12.5 16V8", "M17 16v-7"],
  users:       ["M9 11.5a3.2 3.2 0 1 0 0-6.4 3.2 3.2 0 0 0 0 6.4Z", "M3.5 20a5.5 5.5 0 0 1 11 0", "M16 5.4a3.2 3.2 0 0 1 0 6.2", "M17.5 14.5a5.5 5.5 0 0 1 3 5"],
  settings:    ["M4 7h10", "M18 7h2", "M4 12h2", "M10 12h10", "M4 17h7", "M15 17h5",
                "M16 5.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Z", "M8 10.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Z", "M13 15.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Z"],
  search:      ["M10.5 17a6.5 6.5 0 1 0 0-13 6.5 6.5 0 0 0 0 13Z", "M15.5 15.5 20 20"],
  file:        ["M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8Z", "M14 3v5h5", "M9 13h6", "M9 17h6"],
  database:    ["M12 6.5c4.4 0 8-1.1 8-2.5S16.4 1.5 12 1.5 4 2.6 4 4s3.6 2.5 8 2.5Z", "M4 4v6c0 1.4 3.6 2.5 8 2.5s8-1.1 8-2.5V4", "M4 10v6c0 1.4 3.6 2.5 8 2.5s8-1.1 8-2.5v-6"],
  bell:        ["M18 8.5a6 6 0 1 0-12 0c0 7-3 8.5-3 8.5h18s-3-1.5-3-8.5", "M10.5 20.5a1.8 1.8 0 0 0 3 0"],
  inbox:       ["M4 13 6.5 5.5A2 2 0 0 1 8.4 4h7.2a2 2 0 0 1 1.9 1.5L20 13v5a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z", "M4 13h4l1.5 2.5h5L16 13h4"],
  plus:        ["M12 5v14", "M5 12h14"],
  check:       ["M5 12.5 10 17.5 19.5 7"],
  close:       ["M6 6l12 12", "M18 6 6 18"],
  chevron:     ["M9 5l7 7-7 7"],

  // — theme toggle —
  sun:         ["M8.5 12a3.5 3.5 0 1 0 7 0 3.5 3.5 0 0 0-7 0Z", "M12 2.5V4.5", "M12 19.5v2", "M2.5 12h2", "M19.5 12h2", "M5.4 5.4 6.8 6.8", "M17.2 17.2l1.4 1.4", "M18.6 5.4 17.2 6.8", "M6.8 17.2 5.4 18.6"],
  moon:        ["M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8Z"],
  spark:       ["M12 3 13.8 9 20 10.8 14 12.6 12 21 10 12.6 4 10.8 10.2 9Z"], // brand mark
}

const paths = computed(() => ICONS[props.name] || [])
</script>

<template>
  <svg
    :width="size" :height="size" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" stroke-width="1.5" stroke-linecap="round"
    stroke-linejoin="round" class="ds-icon" aria-hidden="true"
  >
    <path v-for="(d, i) in paths" :key="i" :d="d" />
  </svg>
</template>

<style scoped>
.ds-icon { display: block; flex-shrink: 0; }
</style>
