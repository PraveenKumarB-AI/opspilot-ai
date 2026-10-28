import { useEffect, useState } from 'react'
import { NavLink, Navigate, Route, Routes } from 'react-router-dom'
import { api } from './api'
import Intake from './pages/Intake'
import ReviewQueue from './pages/ReviewQueue'
import Dashboard from './pages/Dashboard'
import Audit from './pages/Audit'
import Baseline from './pages/Baseline'

const NAV = [
  { to: '/intake', label: 'New request', hint: 'Submit and triage' },
  { to: '/queue', label: 'Review queue', hint: 'Approve or escalate' },
  { to: '/dashboard', label: 'Dashboard', hint: 'Time and quality' },
  { to: '/baseline', label: 'Baseline timer', hint: 'Measure manual work' },
  { to: '/audit', label: 'Audit trail', hint: 'Every step logged' },
]

export default function App() {
  const [health, setHealth] = useState(null)
  useEffect(() => { api.health().then(setHealth).catch(() => setHealth({ status: 'down' })) }, [])

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
              <div className="text-sm font-medium">{n.label}</div>
              <div className="text-xs opacity-70">{n.hint}</div>
            </NavLink>
          ))}
        </nav>
        <div className="m-3 rounded-xl bg-white/5 p-3 text-xs text-slate-300 ring-1 ring-white/10">
          <div className="font-medium text-white">System</div>
          {health?.status === 'ok' ? (
            <>
              <div className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_2px_rgb(52_211_153/0.7)]" />API: connected</div>
              <div>Drafting: {health.llm ? 'Claude API' : 'Fallback mode (no API key)'}</div>
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
