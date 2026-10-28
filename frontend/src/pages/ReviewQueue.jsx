import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'
import Journey from '../components/Journey'
import PageHeader from '../components/PageHeader'
import { AutoSendBox, Badge, Button, Card, DraftBadge, EmailPreview, Empty, ErrorBox, Evidence, Field, QueueBadge, Reasons, StatusBadge, inputClass } from '../components/ui'

function readName() { try { return localStorage.getItem('reviewer') || '' } catch { return '' } }
function saveName(v) { try { localStorage.setItem('reviewer', v) } catch { /* storage unavailable */ } }

export default function ReviewQueue() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [filter, setFilter] = useState('pending')
  const [items, setItems] = useState([])
  const [item, setItem] = useState(null)
  const [text, setText] = useState('')
  const [reviewer, setReviewer] = useState(readName)
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [confirmed, setConfirmed] = useState(false)
  const openedAt = useRef(Date.now())

  const loadList = useCallback(() => {
    const params = { pending: { status: 'pending' }, sent: { status: 'sent' }, all: {} }[filter]
    api.listRequests(params).then(setItems).catch((e) => setError(e.message))
  }, [filter])
  useEffect(loadList, [loadList])

  const loadItem = useCallback((requestId, isCurrent = () => true) => {
    return api.getRequest(requestId).then((r) => {
      if (!isCurrent()) return          // a newer click won: ignore this late response
      setItem(r)
      setText(r.review?.final_text || (r.draft?.mode !== 'none' ? r.draft?.draft_text : '') || '')
      setReason(''); setError(''); setConfirmed(false)
      openedAt.current = Date.now()   // review timer starts when the case is opened
    }).catch((e) => { if (isCurrent()) setError(e.message) })
  }, [])

  useEffect(() => {
    if (!id) { setItem(null); return }
    let current = true
    loadItem(id, () => current)
    return () => { current = false }  // runs when id changes: marks the old request as stale
  }, [id, loadItem])

  const decide = async (kind) => {
    const norm = (t) => t.replace(/\r\n/g, '\n').trim()
    const edited = item.draft?.mode !== 'none' && norm(text) !== norm(item.draft.draft_text)
    const action = kind === 'approve' ? (edited || item.draft?.mode === 'none' ? 'edit' : 'approve') : kind
    if (kind === 'approve' && !text.trim()) { setError('Write a reply before approving.'); return }
    if (kind === 'approve' && needsConfirm && !confirmed) { setError('The citation check failed. Tick the box to confirm you checked the draft against the sources.'); return }
    setBusy(true); setError('')
    try {
      saveName(reviewer)
      const updated = await api.review(item.id, {
        action, reviewer, final_text: text, reason,
        seconds_spent: Math.min(7199, Math.max(1, Math.round((Date.now() - openedAt.current) / 1000))), // API: 0 < s < 7200
      })
      setItem(updated); loadList()
    } catch (e) {
      setError(e.message)
      if (/already been reviewed/.test(e.message)) { // show the other reviewer's decision, and keep the explanation
        loadItem(item.id).then(() => setError(`${e.message}. Showing the decision that was saved.`)); loadList()
      }
    }
    finally { setBusy(false) }
  }

  const done = item?.review?.action
  // Only generated answers make factual claims to check; holding replies have none.
  const needsConfirm = ['llm', 'fallback'].includes(item?.draft?.mode) && item?.draft?.citation_ok === false
  return (
    <>
      <PageHeader title="Review queue" subtitle="Cases that need a person, priority first with the reason shown. Safe, routine replies are sent automatically: see Auto-sent." />
      <div className="grid grid-cols-[minmax(0,1fr)] gap-6 lg:grid-cols-3">
        <Card title="Requests" tilt={false} action={
          <div className="flex rounded-lg bg-slate-100 p-0.5 text-xs">
            {[['pending', 'Pending'], ['sent', 'Auto-sent'], ['all', 'All']].map(([f, label]) => (
              <button key={f} onClick={() => setFilter(f)} className={`rounded-md px-3 py-1 ${filter === f ? 'bg-white shadow-sm' : 'text-slate-600'}`}>{label}</button>
            ))}
          </div>}>
          {items.length === 0 ? <Empty>No requests here yet. Submit one from “New request”.</Empty> : (
            <ul className="-my-2 divide-y divide-slate-100">
              {items.map((r) => (
                <li key={r.id}>
                  <button onClick={() => navigate(`/queue/${r.id}`)}
                    className={`w-full rounded-lg px-2 py-3 text-left hover:bg-white/60 ${String(r.id) === id ? 'bg-indigo-50/70' : ''}`}>
                    <div className="flex items-center justify-between gap-2">
                      <span className="truncate text-sm font-medium">#{r.id} {r.subject}</span>
                      {r.queue === 'priority' && <span className="h-2 w-2 shrink-0 rounded-full bg-amber-500" title="Priority" />}
                    </div>
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      <Badge>{r.category}</Badge>
                      {r.risk === 'high' && <Badge tone="red">High risk</Badge>}
                      {filter !== 'pending' && <StatusBadge status={r.status} />}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <div className="space-y-6 lg:col-span-2" aria-live="polite">
          <ErrorBox error={error} />
          {!item ? <Card><Empty>Select a request to review it.</Empty></Card> : (
            <>
              <Card tilt={false} title={`#${item.id}: ${item.subject}`} action={<div className="flex gap-2"><QueueBadge queue={item.review.queue} /><StatusBadge status={item.status} /></div>}>
                <div className="mb-3 text-xs text-slate-500">From {item.customer} · {new Date(item.received_at).toLocaleString()}</div>
                <p className="mb-4 whitespace-pre-wrap rounded-lg bg-white/60 p-3 text-sm">{item.body}</p>
                <div className="mb-5"><Journey request={item} /></div>
                {item.status !== 'sent' && <Reasons reasons={item.review.routing_reasons} />}
                <AutoSendBox audit={item.audit} />
              </Card>

              <Card tilt={false} title={done === 'auto_send' ? 'Reply that was sent (internal copy, with source tags)' : item.draft.mode === 'none' ? 'Reply (no AI draft: write or escalate)' : item.draft.mode === 'holding' ? 'Holding reply: approve to acknowledge the customer, or escalate with a reason' : `Draft reply (${item.draft.mode === 'llm' ? 'written by the LLM' : 'fallback: copied from sources'}): edit before approving if needed`}
                action={<DraftBadge draft={item.draft} />}>
                {needsConfirm && item.draft.issues?.length > 0 && (
                  <div role="alert" className="mb-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
                    <div className="font-semibold">Citation check failed</div>
                    <ul className="list-disc pl-5">{item.draft.issues.map((x) => <li key={x}>{x}</li>)}</ul>
                  </div>
                )}
                <label htmlFor="reply" className="sr-only">Reply text</label>
                <textarea id="reply" className={`${inputClass} font-mono text-[13px] leading-6`} rows={10} value={text} disabled={!!done}
                  onChange={(e) => setText(e.target.value)} placeholder="No safe draft. Write a reply, or escalate to a specialist." />
                {done ? (
                  <div className="mt-4 rounded-lg bg-white/60 p-3 text-sm text-slate-700">
                    {done === 'auto_send' ? <><b>Sent automatically</b> by {item.review.reviewer}: no person needed</> : <>
                      <b className="capitalize">{done}</b> by {item.review.reviewer} in {item.review.seconds_spent ?? '?'}s
                      {item.review.reason && <> · Reason: {item.review.reason}</>}</>}
                  </div>
                ) : (
                  <div className="mt-4 space-y-4">
                    <div className="grid gap-4 sm:grid-cols-2">
                      <Field label="Your name"><input className={inputClass} value={reviewer} onChange={(e) => setReviewer(e.target.value)} /></Field>
                      <Field label="Reason" hint="Required to reject or escalate"><input className={inputClass} value={reason} onChange={(e) => setReason(e.target.value)} /></Field>
                    </div>
                    <details className="rounded-xl bg-white/50 p-3 ring-1 ring-white/80" open>
                      <summary className="cursor-pointer text-sm font-semibold text-slate-700">Sources ({item.draft.citations?.length ? 'highlighted = cited in the draft' : 'none cited'})</summary>
                      <div className="mt-3"><Evidence items={item.evidence} cited={item.draft.citations} /></div>
                    </details>
                    {needsConfirm && (
                      <label className="flex items-start gap-2 text-sm text-rose-800">
                        <input type="checkbox" className="mt-1" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />
                        I checked this draft against the sources and fixed the issues above.
                      </label>
                    )}
                    <div className="flex flex-wrap gap-2">
                      <Button disabled={busy || (needsConfirm && !confirmed)} onClick={() => decide('approve')}>Approve and send</Button>
                      <Button variant="warning" disabled={busy} onClick={() => decide('escalate')}>Escalate to specialist</Button>
                      <Button variant="danger" disabled={busy} onClick={() => decide('reject')}>Reject draft</Button>
                    </div>
                    <p className="text-xs text-slate-500">Prototype: no real email leaves the app. Below is what the customer would receive.</p>
                  </div>
                )}
              </Card>
              {item.email && (
                <Card title={done === 'auto_send' ? 'Email sent to the customer' : done ? 'Email the customer received' : 'Email preview (from the draft; your edits apply when you approve)'}>
                  <EmailPreview email={item.email} to={item.customer} />
                </Card>
              )}
            </>
          )}
        </div>
      </div>
    </>
  )
}
