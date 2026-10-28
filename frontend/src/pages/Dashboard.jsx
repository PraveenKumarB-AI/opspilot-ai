import { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api'
import PageHeader from '../components/PageHeader'
import { Badge, Card, Empty, ErrorBox } from '../components/ui'

function Stat({ label, value, note }) {
  return (
    <div className="glass tilt rounded-2xl p-5">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-2 text-3xl font-semibold tabular-nums">{value}</div>
      {note && <div className="mt-1 text-xs text-slate-500">{note}</div>}
    </div>
  )
}

const pct = (v) => (v == null ? '–' : `${Math.round(v * 100)}%`)
const toRows = (obj) => Object.entries(obj || {}).map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count)

const EVAL_LABELS = {
  category_accuracy_pct: 'Category accuracy',
  retrieval_hit_at_3_pct: 'Right document in top 3',
  citation_correct_pct: 'Drafts passing citation check',
  high_risk_recall_pct: 'High-risk requests caught',
  must_review_recall_pct: 'Must-review cases sent to priority',
  unneeded_priority_pct: 'Clear cases sent to priority anyway',
  drafted_without_answer_pct: 'Drafts written with no answer',
}

export default function Dashboard() {
  const [m, setM] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => { api.metrics().then(setM).catch((e) => setError(e.message)) }, [])
  if (error) return <ErrorBox error={error} />
  if (!m) return <div className="text-sm text-slate-500">Loading…</div>

  const saved = m.time_saved_pct
  return (
    <>
      <PageHeader title="Dashboard" subtitle="Live numbers from this app's database. All data is synthetic." />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <Stat label="Requests" value={m.total_requests} note={`${m.pending} waiting for review`} />
        <Stat label="Auto-resolved" value={pct(m.auto_send_rate)} note={`${m.auto_sent} answered with no person`} />
        <Stat label="Priority review rate" value={pct(m.priority_rate)} note="Share routed by the safety rules" />
        <Stat label="Avg review time" value={m.avg_review_seconds == null ? '–' : `${m.avg_review_seconds}s`}
          note={m.manual_baseline_seconds == null ? 'No manual baseline yet: use Baseline timer' : `Manual baseline ${m.manual_baseline_seconds}s (${m.manual_samples} timed)`} />
        <Stat label="Time saved per request" value={saved == null ? '–' : `${saved}%`}
          note={saved == null ? 'Needs approved reviews + baseline timings' : `Your timings on synthetic tickets (${m.manual_samples} baseline samples)`} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card title="Requests by category" tilt={false}>
          {m.total_requests === 0 ? <Empty>No requests yet.</Empty> : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={toRows(m.by_category)} layout="vertical" margin={{ left: 24 }}>
                <CartesianGrid horizontal={false} stroke="#e2e8f0" />
                <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
                <YAxis type="category" dataKey="name" width={90} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#4f46e5" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>
        <Card title="Decisions (people and automatic)" tilt={false} action={<span className="text-xs text-slate-500">Approved unedited {pct(m.approved_unedited_rate)} · Edited {pct(m.edit_rate)}</span>}>
          {m.reviewed + m.auto_sent === 0 ? <Empty>No decisions yet.</Empty> : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={toRows(m.by_action)}>
                <CartesianGrid vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#0d9488" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>

      <Card className="mt-6" title="Latest evaluation run" action={<Badge tone="amber">Synthetic test set</Badge>}>
        {!m.latest_eval ? <Empty>Run <code className="font-mono">python -m eval.run_eval</code> to fill this in.</Empty> : (
          <>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {Object.entries(EVAL_LABELS).filter(([k]) => k in m.latest_eval.metrics).map(([k, label]) => (
                <div key={k} className="rounded-xl bg-white/60 p-3 ring-1 ring-white/80">
                  <div className="text-xs text-slate-500">{label}</div>
                  <div className="text-xl font-semibold tabular-nums">{m.latest_eval.metrics[k]}%</div>
                </div>
              ))}
            </div>
            <p className="mt-3 text-xs text-slate-500">Run {m.latest_eval.run_id} · {new Date(m.latest_eval.created_at).toLocaleString()} · invented requests, not business results.</p>
          </>
        )}
      </Card>
    </>
  )
}
