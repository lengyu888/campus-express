import { ref } from 'vue'

const KEY = 'ce_motion_pref'
const media = window.matchMedia('(prefers-reduced-motion: reduce)')

/** auto：跟随系统与设备能力；full：强制完整；reduced：强制精简 */
export const motionPref = ref(localStorage.getItem(KEY) || 'auto')
/** full | low | reduced，写入 html[data-motion] 供 CSS 使用 */
export const motionTier = ref('full')

let degraded = false

function computeTier() {
  if (motionPref.value === 'reduced') return 'reduced'
  if (motionPref.value === 'auto' && media.matches) return 'reduced'
  if (motionPref.value === 'full') return degraded ? 'low' : 'full'

  const cores = navigator.hardwareConcurrency || 8
  const memory = navigator.deviceMemory || 8
  if (cores <= 4 || memory <= 4) return 'low'
  return degraded ? 'low' : 'full'
}

export function applyMotion() {
  motionTier.value = computeTier()
  document.documentElement.dataset.motion = motionTier.value
}

export function setMotionPref(value) {
  motionPref.value = value
  localStorage.setItem(KEY, value)
  degraded = false
  applyMotion()
}

export function toggleMotion() {
  setMotionPref(motionTier.value === 'reduced' ? 'full' : 'reduced')
}

function sampleFps() {
  if (motionTier.value === 'reduced' || motionPref.value === 'reduced') return
  let frames = 0
  const start = performance.now()
  const tick = (now) => {
    frames += 1
    if (now - start < 1400) {
      requestAnimationFrame(tick)
      return
    }
    const fps = Math.round((frames * 1000) / (now - start))
    if (fps < 45) {
      degraded = true
      applyMotion()
    }
  }
  requestAnimationFrame(tick)
}

export function initMotion() {
  applyMotion()
  if (media.addEventListener) media.addEventListener('change', applyMotion)
  window.setTimeout(sampleFps, 1600)
}

/* ---------------- 滚动入场 ---------------- */
let observer = null

function getObserver() {
  if (!observer) {
    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-in')
            observer.unobserve(entry.target)
          }
        })
      },
      { threshold: 0.14, rootMargin: '0px 0px -6% 0px' }
    )
  }
  return observer
}

export const vReveal = {
  mounted(el, binding) {
    const delay = typeof binding.value === 'number' ? binding.value : binding.value?.delay || 0
    el.classList.add('rv')
    el.style.setProperty('--rv-delay', `${delay}ms`)

    if (document.documentElement.dataset.motion === 'reduced' || !('IntersectionObserver' in window)) {
      el.classList.add('is-in')
      return
    }
    getObserver().observe(el)
  },
  unmounted(el) {
    observer?.unobserve(el)
  }
}
