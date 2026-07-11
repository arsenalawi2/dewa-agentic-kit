// useFetch — the DAK-standard tiny data hook. GET a same-origin JSON URL with
// loading/error/data state. Extend this (don't duplicate fetch logic per page).
import { useEffect, useState } from "react"

export function useFetch(url, { deps = [] } = {}) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  useEffect(() => {
    let alive = true
    setLoading(true)
    setError(null)
    fetch(url, { credentials: "same-origin" })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d) => alive && (setData(d), setLoading(false)))
      .catch((e) => alive && (setError(e.message), setLoading(false)))
    return () => { alive = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
  return { data, loading, error }
}
