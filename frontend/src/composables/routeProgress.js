import { ref } from 'vue'

export const routeLoading = ref(false)
let timer = null

export function startRoute() {
  window.clearTimeout(timer)
  routeLoading.value = true
}

export function endRoute() {
  window.clearTimeout(timer)
  timer = window.setTimeout(() => {
    routeLoading.value = false
  }, 320)
}
