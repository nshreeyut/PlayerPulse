/**
 * App Component — Root of your component tree
 * =============================================
 * This file defines the top-level structure of your app:
 *   - Which routes exist and what component each renders
 *   - Any layout that wraps every page (e.g., a navbar)
 *
 * React Router replaces traditional server-side routing.
 * <Routes> looks at the current URL and renders the matching <Route>.
 * Navigation is instant — no page reload, no server round-trip.
 *
 * As your app grows, add more <Route> entries here.
 *
 * LEARN MORE:
 *   React Router basics: https://reactrouter.com/en/main/start/overview
 *   useNavigate hook:    https://reactrouter.com/en/main/hooks/use-navigate
 */

import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Demo from './pages/Demo'

function App() {
  return (
    <div className="app">
      <Routes>
        {/* Home page — player search + analytics + chat (real data pipeline) */}
        <Route path="/" element={
          <main>
            <Home />
          </main>
        } />

        {/* Demo page — synthetic data, no API key required */}
        <Route path="/demo" element={<Demo />} />
      </Routes>
    </div>
  )
}

export default App
