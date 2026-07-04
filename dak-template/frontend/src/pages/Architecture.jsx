import { Card } from "@astryxdesign/core/Card"
import { Text } from "@astryxdesign/core/Text"
import { Heading } from "@astryxdesign/core/Heading"
import { Badge } from "@astryxdesign/core/Badge"
import { VStack } from "@astryxdesign/core/VStack"
import { useFetch } from "../lib/useFetch.js"

// /architecture — reads public/tech-stack.json (auto-detected by the leaderboard
// hook from package.json / requirements.txt / docker-compose; hand-curate extras).
export default function Architecture() {
  const { data, loading } = useFetch("/tech-stack.json")
  // Tolerant: accept {categories:[{name,items:[]}]} or {stack:{cat:[...]}} or a flat list.
  const cats = data?.categories
    || (data?.stack ? Object.entries(data.stack).map(([name, items]) => ({ name, items })) : [])
    || []

  return (
    <div className="page-band">
      <span className="eyebrow">Project</span>
      <Heading level={1} type="display-3">Architecture</Heading>
      <Text color="secondary" size="lg">The tech stack powering this app.</Text>
      <div className="auto-grid" style={{ marginTop: "var(--spacing-6)" }}>
        {loading && <Text color="secondary">Loading…</Text>}
        {!loading && cats.length === 0 && <Text color="secondary">No stack yet — update public/tech-stack.json.</Text>}
        {cats.map((c, i) => (
          <Card key={i} padding={4}>
            <VStack gap={2}>
              <Text weight="semibold">{c.name || c.category}</Text>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--spacing-1)" }}>
                {(c.items || c.technologies || []).map((t, j) => (
                  <Badge key={j} variant="neutral" label={typeof t === "string" ? t : t.name} />
                ))}
              </div>
            </VStack>
          </Card>
        ))}
      </div>
    </div>
  )
}
