/**
 * API Client — Central HTTP Configuration
 * =========================================
 * All API calls go through this configured axios instance.
 *
 * WHY CENTRALIZE THIS?
 * ---------------------
 * If your backend URL changes (Render → Railway, port changes, etc.),
 * you change it in ONE place here — not scattered across components.
 *
 * HOW THE BASE URL WORKS:
 * ------------------------
 * Development (VITE_API_URL not set):
 *   baseURL = ""  →  requests go to the same origin (localhost:5173)
 *   Vite's proxy in vite.config.js then forwards /api/* to localhost:8000
 *
 * Production (VITE_API_URL set to Render URL in Vercel env vars):
 *   baseURL = "https://your-api.onrender.com"
 *   Requests go directly to Render — no proxy needed
 *
 * You never change any component code between dev and prod. Just the env var.
 *
 * INTERCEPTORS:
 * -------------
 * Interceptors run automatically on every request/response.
 * They're the right place for:
 *   - Attaching auth tokens (request interceptor)
 *   - Logging all errors in one place (response interceptor)
 *   - Redirecting to login on 401 (response interceptor)
 */

import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  headers: {
    'Content-Type': 'application/json',
  },
  // Live player lookups collect real API data (Riot: up to 20 matches × 1.3s each = ~30s).
  // Set to 90s to give the backend enough room.
  timeout: 90000,
})

// ---------------------------------------------------------
// Request Interceptor
// ---------------------------------------------------------
// Runs BEFORE every request is sent.
client.interceptors.request.use(
  (config) => {
    // TODO: If you add user authentication, attach the token here:
    // const token = localStorage.getItem('token')
    // if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  },
  (error) => Promise.reject(error)
)

// ---------------------------------------------------------
// Response Interceptor
// ---------------------------------------------------------
// Runs AFTER every response is received.
client.interceptors.response.use(
  (response) => response,
  (error) => {
    // Log errors globally so you don't have to repeat this in every component
    console.error(
      `API Error: ${error.response?.status} on ${error.config?.url}`,
      error.response?.data
    )
    // TODO: If you get a 401 Unauthorized, redirect to a login page:
    // if (error.response?.status === 401) window.location.href = '/login'
    return Promise.reject(error)
  }
)

export default client
