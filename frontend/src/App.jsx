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
      <aside className="hidden w-64 shrink-0 flex-col border-r border-slate-200 bg-white md:flex">
        <div className="px-6 py-5">
          <div className="flex items-center gap-2">
            <div className="grid h-8 w-8 place-items-center rounded-lg bg-indigo-600 text-sm font-bold text-white">OP</div>
            <div>
              <div className="text-sm font-semibold">OpsPilot AI</div>
              <div className="text-xs text-slate-500">Support assistant</div>
            </div>
          </div>
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to}
              className={({ isActive }) => `block rounded-lg px-3 py-2 ${isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-700 hover:bg-slate-50'}`}>
              <div className="text-sm font-medium">{n.label}</div>
              <div className="text-xs text-slate-500">{n.hint}</div>
            </NavLink>
          ))}
        </nav>
        <div className="m-3 rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
          <div className="font-medium text-slate-700">System</div>
          {health?.status === 'ok' ? (
            <>
              <div>API: connected</div>
              <div>Drafting: {health.llm ? 'Claude API' : 'Fallback mode (no API key)'}</div>
              <div>Search: {health.embeddings}</div>
            </>
          ) : health ? <div className="text-rose-700">API not reachable. Is uvicorn running?</div> : <div>Checking…</div>}
          <div className="mt-2 text-slate-500">Synthetic data only.</div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <nav className="flex gap-1 overflow-x-auto border-b border-slate-200 bg-white px-3 py-2 md:hidden">
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
