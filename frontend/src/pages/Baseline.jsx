import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import PageHeader from '../components/PageHeader'
import { Button, Card, ErrorBox, Field, inputClass } from '../components/ui'

// A stopwatch for measuring how long a request takes WITHOUT the assistant.
export default function Baseline() {
  const [samples, setSamples] = useState([])
  const [pick, setPick] = useState('')
  const [running, setRunning] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const [saved, setSaved] = useState([])
  const [error, setError] = useState('')
  const start = useRef(0)

  useEffect(() => { api.samples().then((s) => setSamples(s.filter((x) => x.type === 'normal'))).catch(() => {}) }, [])
  useEffect(() => {
    if (!running) return
    const t = setInterval(() => setElapsed(Math.round((Date.now() - start.current) / 1000)), 250)
    return () => clearInterval(t)
  }, [running])

  const ticket = samples.find((s) => s.id === pick)
  const begin = () => { start.current = Date.now(); setElapsed(0); setRunning(true) }
  const stop = async () => {
    setRunning(false)
    const seconds = Math.min(7199, Math.max(1, Math.round((Date.now() - start.current) / 1000))) // API: 0 < s < 7200
    try { await api.addTiming({ ticket_ref: pick, seconds }); setSaved((s) => [{ ref: pick, seconds }, ...s]) }
    catch (e) { setError(e.message) }
  }
  const mm = String(Math.floor(elapsed / 60)).padStart(2, '0'), ss = String(elapsed % 60).padStart(2, '0')

  return (
    <>
      <PageHeader title="Baseline timer" subtitle="Measure how long a request takes by hand, before using the assistant. These timings feed the time-saved figure on the dashboard." />
      <div className="grid grid-cols-[minmax(0,1fr)] gap-6 lg:grid-cols-3">
        <Card title="How to measure" className="lg:col-span-1">
          <ol className="list-decimal space-y-2 pl-5 text-sm text-slate-700">
            <li>Pick a request you have not seen before.</li>
            <li>Press Start, then handle it manually: read it, search the knowledge files in <code>data/knowledge</code>, and write a full reply in a text editor.</li>
            <li>Press Stop when the reply is ready to send.</li>
            <li>Time at least 10 requests. Then use different requests in the assistant so you are not timing ones you already know.</li>
          </ol>
          <p className="mt-4 text-xs text-slate-500">In a real team, the baseline comes from shadowing agents and ticket timestamps, not one person.</p>
        </Card>
        <Card title="Stopwatch" className="lg:col-span-2" tilt={false}>
          <Field label="Request to handle manually">
            <select className={inputClass} value={pick} onChange={(e) => setPick(e.target.value)} disabled={running}>
              <option value="">Choose…</option>
              {samples.map((s) => <option key={s.id} value={s.id}>{s.id} · {s.subject}</option>)}
            </select>
          </Field>
          {ticket && <p className="mt-3 rounded-xl bg-white/60 p-3 text-sm">{ticket.body}</p>}
          <div className="my-6 text-center font-mono text-6xl font-semibold tabular-nums text-indigo-900 drop-shadow-sm" role="timer" aria-live="off">{mm}:{ss}</div>
          <div className="flex justify-center gap-3">
            {!running ? <Button disabled={!pick} onClick={begin}>Start</Button> : <Button variant="danger" onClick={stop}>Stop and save</Button>}
          </div>
          <ErrorBox error={error} />
          {saved.length > 0 && (
            <ul className="mt-6 divide-y divide-slate-100 text-sm">
              {saved.map((s, i) => <li key={i} className="flex justify-between py-2"><span>{s.ref}</span><span className="tabular-nums">{s.seconds}s</span></li>)}
            </ul>
          )}
        </Card>
      </div>
    </>
  )
}
