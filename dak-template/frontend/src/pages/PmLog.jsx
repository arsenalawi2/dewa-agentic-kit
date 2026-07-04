import { useEffect, useMemo, useRef } from "react"
import { marked } from "marked"
import mermaid from "mermaid"
import { Heading } from "@astryxdesign/core/Heading"
import { Text } from "@astryxdesign/core/Text"
import pmSource from "@pmlog?raw"

// /pm-log — renders PROJECT.md (repo root) directly via marked + mermaid.
// Edit PROJECT.md, this page updates. No intermediate JSON.
export default function PmLog() {
  const ref = useRef(null)
  const html = useMemo(() => marked.parse(pmSource || "# PROJECT.md\n\nAdd your project log here."), [])

  useEffect(() => {
    const root = ref.current
    if (!root) return
    // Turn ```mermaid fences into <div class="mermaid"> then render them.
    root.querySelectorAll("code.language-mermaid").forEach((code) => {
      const div = document.createElement("div")
      div.className = "mermaid"
      div.textContent = code.textContent
      code.closest("pre")?.replaceWith(div)
    })
    try {
      mermaid.initialize({ startOnLoad: false, theme: "neutral" })
      mermaid.run({ nodes: root.querySelectorAll(".mermaid") })
    } catch { /* diagrams optional */ }
  }, [html])

  return (
    <div className="page-band">
      <span className="eyebrow">Project</span>
      <Heading level={1} type="display-3">PM Log</Heading>
      <Text color="secondary" size="lg">The project management log — rendered from PROJECT.md.</Text>
      <div ref={ref} className="prose" style={{ marginTop: "var(--spacing-6)" }} dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  )
}
