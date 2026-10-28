import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import Journey from '../components/Journey'
import PageHeader from '../components/PageHeader'
import { AutoSendBox, Badge, Button, Card, DraftBadge, DraftText, EmailPreview, Empty, ErrorBox, Evidence, Field, QueueBadge, Reasons, StatusBadge, inputClass } from '../components/ui'

export default function Intake() {
  const [samples, setSamples] = useState([])
  const [form, setForm] = useState({ customer: 'Demo customer', subject: '', body: '' })
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => { api.samples().then(setSamples).catch((e) => setError(`Examples could not load. ${e.message}`)) }, [])

  const pickSample = (id) => {
    const s = samples.find((x) => x.id === id)
    if (s) setForm({ ...form, subject: s.subject, body: s.body })
  }

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError(''); setResult(null)
    try { setResult(await api.createRequest(form)) }
    catch (err) { setError(err.message) }
    finally { setBusy(false) }
  }

  return (
    <>
      <PageHeader title="New request" subtitle="Paste a customer request. OpsPilot classifies it, finds sources and drafts a cited reply. Safe, routine cases are answered automatically; everything else goes to a person." />
      <div className="grid gap-6 lg:grid-cols-5">
        <Card title="Customer request" className="lg:col-span-2">
          <form onSubmit={submit} className="space-y-4">
            <Field label="Load a synthetic example" hint="52 invented requests: normal, ambiguous, unsupported, high-risk and adversarial.">
              <select className={inputClass} defaultValue="" onChange={(e) => pickSample(e.target.value)}>
                <option value="" disabled>Choose an example…</option>
                {['normal', 'ambiguous', 'unsupported', 'high_risk', 'adversarial'].map((t) => (
                  <optgroup key={t} label={t.replace('_', ' ')}>
                    {samples.filter((s) => s.type === t).map((s) => <option key={s.id} value={s.id}>{s.id} · {s.subject}</option>)}
                  </optgroup>
                ))}
              </select>
            </Field>
            <Field label="Customer">
              <input className={inputClass} value={form.customer} onChange={(e) => setForm({ ...form, customer: e.target.value })} />
            </Field>
            <Field label="Subject">
              <input className={inputClass} required value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} />
            </Field>
            <Field label="Message">
              <textarea className={inputClass} required rows={6} value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} />
            </Field>
            <ErrorBox error={error} />
            <Button type="submit" disabled={busy} className="w-full">{busy ? 'Processing…' : 'Process request'}</Button>
          </form>
        </Card>

        <div className="space-y-6 lg:col-span-3" aria-live="polite">
          {!result ? (
            <Card title="Ticket journey" tilt={false}>
              <Journey />
              <p className="mt-5 text-sm text-slate-600">Load an example or paste a request, then process it. You'll see each stage it passes through, and whether it was emailed automatically or handed to a person.</p>
            </Card>
          ) : (
            <>
              <Card tilt={false} title={`Request #${result.id}: ${result.subject}`} action={result.status === 'sent' ? <StatusBadge status="sent" /> : <QueueBadge queue={result.review.queue} />}>
                <Journey request={result} />
                <div className="mt-5" />
                {result.status !== 'sent' && <Reasons reasons={result.review.routing_reasons} />}
                <AutoSendBox audit={result.audit} />
                <div className="mt-4 flex justify-end">
                  <Button variant="secondary" onClick={() => navigate(`/queue/${result.id}`)}>{result.status === 'sent' ? 'View in queue →' : 'Open in review queue →'}</Button>
                </div>
              </Card>
              <Card title={result.draft.mode === 'holding' ? 'Draft reply (holding reply: a person handles the answer)' : 'Draft reply'} action={<DraftBadge draft={result.draft} />}>
                {result.draft.mode === 'none'
                  ? <Empty>{result.draft.draft_text}</Empty>
                  : <DraftText text={result.draft.draft_text} />}
              </Card>
              {result.email && (
                <Card title={result.status === 'sent' ? 'Email sent to the customer' : 'Email preview (sent after a person approves)'}>
                  <EmailPreview email={result.email} to={result.customer} />
                </Card>
              )}
              <Card title="Sources found"><Evidence items={result.evidence} /></Card>
            </>
          )}
        </div>
      </div>
    </>
  )
}
