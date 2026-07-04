import { Card } from "@astryxdesign/core/Card"
import { Text } from "@astryxdesign/core/Text"
import { Heading } from "@astryxdesign/core/Heading"
import { VStack } from "@astryxdesign/core/VStack"
import { useFetch } from "../lib/useFetch.js"

// /vibe-code — reads public/vibe-stats.json, written by the leaderboard hook
// after every Claude Code session. Never hardcode these numbers.
const fmt = (v) => (typeof v === "number" ? v.toLocaleString("en-US") : v)
const LABELS = {
  sessions: "Sessions", total_prompts: "Prompts", prompts: "Prompts", lines_written: "Lines written",
  total_lines: "Lines written", cost: "Cost", total_cost: "Cost", files: "Files", source_lines: "Source size",
}

export default function VibeCode() {
  const { data, loading } = useFetch("/vibe-stats.json")
  const stats = data && typeof data === "object"
    ? Object.entries(data).filter(([, v]) => typeof v === "number" || typeof v === "string")
    : []

  return (
    <div className="page-band">
      <span className="eyebrow">Project</span>
      <Heading level={1} type="display-3">Vibe Code</Heading>
      <Text color="secondary" size="lg">How this app was built with Claude Code — updated every session.</Text>
      <div className="auto-grid" style={{ marginTop: "var(--spacing-6)" }}>
        {loading && <Text color="secondary">Loading…</Text>}
        {!loading && stats.length === 0 && <Text color="secondary">No stats yet — they appear after your first session.</Text>}
        {stats.map(([k, v]) => (
          <Card key={k} padding={4}>
            <VStack gap={1}>
              <Text size="sm" color="secondary" weight="medium">{LABELS[k] || k.replace(/_/g, " ")}</Text>
              <div className="kpi-value">{fmt(v)}</div>
            </VStack>
          </Card>
        ))}
      </div>
    </div>
  )
}
