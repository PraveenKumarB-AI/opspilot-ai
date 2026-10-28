import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import PageHeader from '../components/PageHeader'
import { Badge, Card, Empty, ErrorBox, inputClass } from '../components/ui'

const TONE = { request_received: 'gray', classified: 'blue', retrieved: 'blue', drafted: 'blue', routed: 'amber', reviewed: 'green', auto_sent: 'green', needs_person: 'gray', pipeline_error: 'red' }

function summarize(event, d) {
  if (event === 'classified') return `${d.category} · ${d.risk} risk · confidence ${d.confidence}`
  if (event === 'retrieved') return d.chunks.join(', ')
  if (event === 'drafted') return `${d.mode}${d.issues?.length ? ' · ' + d.issues.join('; ') : ''}`
  if (event === 'routed') return `${d.queue}${d.reasons.length ? ': ' + d.reasons.join('; ') : ''}`
  if (event === 'reviewed') return `${d.action} by ${d.reviewer}${d.reason ? ' · ' + d.reason : ''}${d.seconds_spent ? ` · ${d.seconds_spent}s` : ''}`
  if (event === 'auto_sent') return `sent automatically · all ${d.checks.length} checks passed`
  if (event === 'needs_person') return `needs a person: ${d.failed.join('; ')}`
  if (event === 'pipeline_error') return `${d.error}: ${d.message}`
  return `${d.customer || ''} via ${d.channel || ''}`
}

export default function Audit() {
  const [rows, setRows] = useState([])
  const [filter, setFilter] = useState('')
  const [error, setError] = useState('')
  useEffect(() => { api.audit().then(setRows).catch((e) => setError(e.message)) }, [])
  const shown = filter ? rows.filter((r) => String(r.request_id) === filter.trim()) : rows

  return (
    <>
      <PageHeader title="Audit trail" subtitle="Append-only log of every step, from request to approver. The database blocks edits and deletes.">
        <input className={`${inputClass} w-48`} placeholder="Filter by request #" value={filter} onChange={(e) => setFilter(e.target.value)} />
      </PageHeader>
      <ErrorBox error={error} />
      <Card tilt={false}>
        {shown.length === 0 ? <Empty>No events yet.</Empty> : (
          <div className="-m-5 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-white/50 text-left text-xs uppercase tracking-wide text-slate-500">
                <tr><th className="px-5 py-3">Time</th><th className="px-5 py-3">Request</th><th className="px-5 py-3">Event</th><th className="px-5 py-3">Details</th></tr>
              </thead>
              <tbody className="divide-y divide-white/70">
                {shown.map((r) => {
                  const d = JSON.parse(r.details)
                  return (
                    <tr key={r.id} className="align-top">
                      <td className="whitespace-nowrap px-5 py-3 text-slate-500">{new Date(r.created_at).toLocaleString()}</td>
                      <td className="px-5 py-3"><Link className="text-indigo-700 hover:underline" to={`/queue/${r.request_id}`}>#{r.request_id}</Link></td>
                      <td className="px-5 py-3"><Badge tone={TONE[r.event] || 'gray'}>{r.event.replaceAll('_', ' ')}</Badge></td>
                      <td className="px-5 py-3 text-slate-700">{summarize(r.event, d)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  )
}
