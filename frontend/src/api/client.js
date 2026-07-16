import axios from 'axios'

const isDesktop =
  typeof window !== 'undefined' &&
  (
    window.__TAURI__ ||
    window.__TAURI_IPC__ ||
    window.__TAURI_INTERNALS__ ||
    window.location.protocol === 'tauri:' ||
    window.location.hostname === 'tauri.localhost' ||
    window.location.hostname.endsWith('.tauri.localhost')
  )
const fallbackDesktopURL = 'http://127.0.0.1:8765'
const isDev = import.meta.env.DEV
const baseURL = (isDesktop || !isDev)
  ? fallbackDesktopURL
  : (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000')
let desktopURLPromise = null

const resolveDesktopURL = async () => {
  if (!isDesktop) return baseURL
  if (window.__CIVILAI_BACKEND_URL__) return window.__CIVILAI_BACKEND_URL__
  if (!desktopURLPromise) {
    const invokeFromWindow = window.__TAURI__?.tauri?.invoke || window.__TAURI__?.invoke
    desktopURLPromise = (invokeFromWindow
      ? Promise.resolve(invokeFromWindow('backend_url'))
      : import('@tauri-apps/api/tauri').then(({ invoke }) => invoke('backend_url')))
      .then((url) => url || fallbackDesktopURL)
      .catch(() => fallbackDesktopURL)
  }
  return desktopURLPromise
}

export const api = axios.create({ baseURL })

// Attach JWT on every request
api.interceptors.request.use(async (config) => {
  const resolvedBaseURL = await resolveDesktopURL()
  config.baseURL = resolvedBaseURL
  const token = localStorage.getItem('civilai_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Bounce to login on auth failure
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response && [401, 403].includes(err.response.status)) {
      const onLogin = window.location.pathname === '/login' || window.location.hash.includes('/login')
      if (!onLogin) {
        localStorage.removeItem('civilai_token')
        localStorage.removeItem('civilai_user')
        window.location.hash = '#/login'
      }
    }
    return Promise.reject(err)
  }
)

// The backend wraps payloads as { status, status_code, message, results }.
// `results` is a list for collections and an object for single records.
export const unwrap = (res) => res?.data?.results

export const errMessage = (err) => {
  const m = err?.response?.data?.message
  if (typeof m === 'string') return m
  if (m && typeof m === 'object') return Object.values(m).flat().join(' ')
  return err?.message || 'Something went wrong'
}
