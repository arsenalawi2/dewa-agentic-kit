import { Card } from "@astryxdesign/core/Card"
import { Text } from "@astryxdesign/core/Text"
import { Heading } from "@astryxdesign/core/Heading"
import { Badge } from "@astryxdesign/core/Badge"
import { Banner } from "@astryxdesign/core/Banner"
import { VStack } from "@astryxdesign/core/VStack"
import { Table, proportional, pixel } from "@astryxdesign/core/Table"
import { Aed } from "../dewa/Aed.jsx"
import { useFetch } from "../lib/useFetch.js"

// KPI card — the starter dashboard shape. Copy this for your own metrics.
function Kpi({ label, value, sub }) {
  return (
    <Card padding={4}>
      <VStack gap={1}>
        <Text size="sm" color="secondary" weight="medium">{label}</Text>
        <div className="kpi-value">{value}</div>
        {sub && <Text size="sm" color="secondary">{sub}</Text>}
      </VStack>
    </Card>
  )
}

const columns = [
  { key: "name", header: "Item", width: proportional({ minWidth: 200 }), renderCell: (r) => <Text weight="semibold">{r.name}</Text> },
  { key: "status", header: "Status", width: pixel(120), renderCell: (r) => <Badge variant={r.status === "active" ? "success" : "neutral"} label={r.status || "—"} /> },
  { key: "price", header: "Price", width: pixel(120), align: "end", renderCell: (r) => <Aed usd={r.price || 0} /> },
]

export default function Home() {
  // The DAK backend ships a sample /api/items resource (dak add-model to add more).
  const { data, error } = useFetch("/api/items")
  const items = Array.isArray(data) ? data : data?.items || []

  return (
    <div className="page-band page-band--wide">
      <div style={{ marginBottom: "var(--spacing-6)" }}>
        <span className="eyebrow">DEWA · Astryx</span>
        <Heading level={1} type="display-3">{`{{PROJECT_NAME}}`}</Heading>
        <Text color="secondary" size="lg">Your new app — DEWA-themed Astryx, with the AED dirham glyph built in.</Text>
      </div>

      <Banner status="info" title="Starter dashboard"
        description="Replace this with your app. KPI cards, an items table from /api/items, and the <Aed> money component are here as a pattern to copy." />

      <div className="auto-grid" style={{ marginTop: "var(--spacing-5)" }}>
        <Kpi label="Items" value={items.length} sub="from /api/items" />
        <Kpi label="Active" value={items.filter((i) => i.status === "active").length} sub="status = active" />
        <Kpi label="Total value" value={<Aed usd={items.reduce((s, i) => s + (i.price || 0), 0)} compact />} sub="sum of prices" />
        <Kpi label="Theme" value="DEWA" sub="Astryx neutral + #007560" />
      </div>

      <Heading level={3} style={{ margin: "var(--spacing-6) 0 var(--spacing-3)" }}>Items</Heading>
      {error && <Banner status="warning" title="Couldn't load items" description={`The backend may not be running yet (${error}).`} />}
      <Card padding={0}>
        <Table data={items} columns={columns} density="balanced" dividers="rows" hasHover idKey="name" />
      </Card>
    </div>
  )
}
