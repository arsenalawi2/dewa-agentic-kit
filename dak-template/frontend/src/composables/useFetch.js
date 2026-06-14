import { ref } from "vue"

// Minimal fetch composable — the shape DAK views use to load JSON.
//   const { data, error, loading, run } = useFetch("/api/items")
//   onMounted(run)
export function useFetch(url) {
  const data = ref(null)
  const error = ref(null)
  const loading = ref(false)

  async function run() {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(url)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      data.value = await res.json()
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  return { data, error, loading, run }
}
