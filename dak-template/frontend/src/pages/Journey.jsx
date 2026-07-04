import { Card } from "@astryxdesign/core/Card"
import { Text } from "@astryxdesign/core/Text"
import { Heading } from "@astryxdesign/core/Heading"
import { Badge } from "@astryxdesign/core/Badge"
import { VStack } from "@astryxdesign/core/VStack"
import { HStack } from "@astryxdesign/core/HStack"
import { useFetch } from "../lib/useFetch.js"

// /journey — the auto-updating build timeline. Reads public/journey-data.json
// (you update it after significant work; see ~/.claude/templates/journey.md).
const STATUS = { done: "success", "in-progress": "info", planned: "neutral", blocked: "error" }

export default function Journey() {
  const { data, loading } = useFetch("/journey-data.json")
  const phases = data?.phases || []
  return (
    <div className="page-band">
      <span className="eyebrow">Project</span>
      <Heading level={1} type="display-3">Journey</Heading>
      <Text color="secondary" size="lg">{data?.summary || "The build timeline — phases and milestones."}</Text>
      <VStack gap={3} style={{ marginTop: "var(--spacing-6)" }}>
        {loading && <Text color="secondary">Loading…</Text>}
        {!loading && phases.length === 0 && <Text color="secondary">No phases yet — update public/journey-data.json.</Text>}
        {phases.map((p, i) => (
          <Card key={i} padding={4}>
            <HStack justify="between" align="start" gap={3} wrap="wrap">
              <VStack gap={1} style={{ minWidth: 0 }}>
                <HStack gap={2} align="center" wrap="wrap">
                  <Text weight="semibold" size="lg">{p.title || p.name || `Phase ${i + 1}`}</Text>
                  {p.status && <Badge variant={STATUS[p.status] || "neutral"} label={p.status} />}
                </HStack>
                {p.summary && <Text color="secondary">{p.summary}</Text>}
              </VStack>
              {p.date && <Text size="sm" color="secondary" className="mono">{p.date}</Text>}
            </HStack>
          </Card>
        ))}
      </VStack>
    </div>
  )
}
