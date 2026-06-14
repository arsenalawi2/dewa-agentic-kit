// Small pure helpers. Grep target for "do we already have a formatter?".
// import { formatNumber, formatDate } from "@/utils/format"

export function formatNumber(n) {
  if (n == null || Number.isNaN(Number(n))) return "—"
  return new Intl.NumberFormat().format(n)
}

export function formatDate(iso) {
  if (!iso) return ""
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? "" : d.toLocaleDateString()
}
