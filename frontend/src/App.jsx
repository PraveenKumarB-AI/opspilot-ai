import { useEffect, useState } from 'react'
import { NavLink, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { api } from './api'
import Intake from './pages/Intake'
import ReviewQueue from './pages/ReviewQueue'
import Dashboard from './pages/Dashboard'
import Audit from './pages/Audit'
import Baseline from './pages/Baseline'

const NAV = [
  { to: '/intake', label: 'New request', hint: 'Process a ticket' },
  { to: '/queue', label: 'Review queue', hint: 'Cases that need a person', count: 'pending' },
  { to: '/dashboard', label: 'Dashboard', hint: 'Time and quality' },
  { to: '/baseline', label: 'Baseline timer', hint: 'Measure manual work' },
  { to: '/audit', label: 'Audit trail', hint: 'Every step logged' },
]

export default function App() {
  const [health, setHealth] = useState(null)
  const [counts, setCounts] = useState(null)
  const location = useLocation()
  useEffect(() => { api.health().then(setHealth).catch(() => setHealth({ status: 'down' })) }, [])
  // Refresh the live counts whenever the page changes, so the sidebar matches what was just done.
  useEffect(() => { api.metrics().then(setCounts).catch(() => {}) }, [location.pathname])
  useEffect(() => {
    const refresh = () => api.metrics().then(setCounts).catch(() => {})
    window.addEventListener('opspilot:changed', refresh)
    return () => window.removeEventListener('opspilot:changed', refresh)
  }, [])

  return (
    <div className="flex min-h-screen">
      <aside className="glass-dark sticky top-0 hidden h-screen w-64 shrink-0 flex-col text-slate-200 md:flex">
        <div className="px-6 py-5">
          <div className="flex items-center gap-2">
            <div className="logo-3d grid h-9 w-9 place-items-center rounded-xl text-sm font-bold text-white">OP</div>
            <div>
              <div className="text-sm font-semibold text-white">OpsPilot AI</div>
              <div className="text-xs text-indigo-200/80">Support assistant</div>
            </div>
          </div>
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to}
              className={({ isActive }) => `block rounded-xl px-3 py-2 transition ${isActive ? 'bg-gradient-to-r from-indigo-500/90 to-violet-500/80 text-white shadow-lg shadow-indigo-900/40 ring-1 ring-white/20' : 'text-slate-300 hover:bg-white/10 hover:text-white'}`}>
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-medium">{n.label}</span>
                {n.count && counts?.[n.count] > 0 && (
                  <span className="rounded-full bg-amber-400 px-2 py-0.5 text-[11px] font-bold text-amber-950 shadow" aria-label={`${counts[n.count]} waiting`}>{counts[n.count]}</span>
                )}
              </div>
              <div className="text-xs opacity-70">{n.hint}</div>
            </NavLink>
          ))}
        </nav>
        {counts && (
          <div className="mx-3 mb-2 grid grid-cols-2 gap-2 text-center">
            <div className="rounded-xl bg-teal-400/10 px-2 py-2 ring-1 ring-teal-300/20">
              <div className="text-xl font-semibold text-teal-200">{counts.auto_sent}</div>
              <div className="text-[11px] text-teal-100/80">emailed automatically</div>
            </div>
            <div className="rounded-xl bg-amber-400/10 px-2 py-2 ring-1 ring-amber-300/20">
              <div className="text-xl font-semibold text-amber-200">{counts.pending}</div>
              <div className="text-[11px] text-amber-100/80">waiting for a person</div>
            </div>
          </div>
        )}
        <div className="m-3 mt-1 rounded-xl bg-white/5 p-3 text-xs text-slate-300 ring-1 ring-white/10">
          <div className="font-medium text-white">System</div>
          {health?.status === 'ok' ? (
            <>
              <div className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_2px_rgb(52_211_153/0.7)]" />API: connected</div>
              <div>Drafting: {health.llm_label || (health.llm ? 'LLM' : 'Fallback mode (no API key)')}</div>
              <div>Search: {health.embeddings}</div>
            </>
          ) : health ? <div className="flex items-center gap-1.5 text-rose-300"><span className="h-2 w-2 rounded-full bg-rose-400 shadow-[0_0_8px_2px_rgb(251_113_133/0.7)]" />API not reachable. Is uvicorn running?</div> : <div>Checking…</div>}
          <div className="mt-2 text-slate-400">Synthetic data only.</div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <nav className="glass flex gap-1 overflow-x-auto px-3 py-2 md:hidden">
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to}
              className={({ isActive }) => `whitespace-nowrap rounded-md px-3 py-1.5 text-sm ${isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600'}`}>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <main className="mx-auto w-full max-w-7xl flex-1 p-4 md:p-8">
          <Routes>
            <Route path="/" element={<Navigate to="/intake" replace />} />
            <Route path="/intake" element={<Intake />} />
            <Route path="/queue" element={<ReviewQueue />} />
            <Route path="/queue/:id" element={<ReviewQueue />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/baseline" element={<Baseline />} />
            <Route path="/audit" element={<Audit />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
