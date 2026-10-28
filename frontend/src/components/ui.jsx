// Small shared building blocks so every page looks consistent.

import { useRef } from 'react'

// Glass card that leans slightly towards the pointer (max 3 degrees) for a 3D feel.
export function Card({ title, action, children, className = '', tilt = true }) {
  const ref = useRef(null)
  const move = (e) => {
    if (!tilt || !ref.current) return
    const r = ref.current.getBoundingClientRect()
    const x = (e.clientX - r.left) / r.width - 0.5
    const y = (e.clientY - r.top) / r.height - 0.5
    ref.current.style.setProperty('--ry', `${(x * 3).toFixed(2)}deg`)
    ref.current.style.setProperty('--rx', `${(-y * 3).toFixed(2)}deg`)
  }
  const leave = () => {
    ref.current?.style.setProperty('--rx', '0deg')
    ref.current?.style.setProperty('--ry', '0deg')
  }
  return (
    <section ref={ref} onMouseMove={move} onMouseLeave={leave}
      className={`glass rounded-2xl ${tilt ? 'tilt' : ''} ${className}`}>
      {title && (
        <header className="flex items-center justify-between border-b border-white/70 px-5 py-3">
          <h2 className="text-sm font-semibold tracking-tight text-slate-800">{title}</h2>
          {action}
        </header>
      )}
      <div className="p-5">{children}</div>
    </section>
  )
}

const TONES = {
  gray: 'bg-gradient-to-b from-white to-slate-100 text-slate-700 ring-slate-200',
  blue: 'bg-gradient-to-b from-white to-indigo-100 text-indigo-700 ring-indigo-200',
  green: 'bg-gradient-to-b from-white to-emerald-100 text-emerald-700 ring-emerald-200',
  amber: 'bg-gradient-to-b from-white to-amber-100 text-amber-800 ring-amber-300',
  red: 'bg-gradient-to-b from-white to-rose-100 text-rose-700 ring-rose-200',
}

export function Badge({ tone = 'gray', children }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium shadow-sm ring-1 ring-inset ${TONES[tone]}`}>
      {children}
    </span>
  )
}

// Unknown values must never look safe, so every known value is listed and anything else is "Unknown".
export function QueueBadge({ queue }) {
  if (queue === 'priority') return <Badge tone="amber">Priority review</Badge>
  if (queue === 'standard') return <Badge tone="blue">Standard review</Badge>
  return <Badge tone="amber">Queue unknown</Badge>
}

export function RiskBadge({ risk }) {
  if (risk === 'high') return <Badge tone="red">High risk</Badge>
  if (risk === 'low') return <Badge tone="green">Low risk</Badge>
  return <Badge tone="amber">Risk unknown</Badge>
}

export function ConfidenceBadge({ classification }) {
  const low = classification.low_confidence !== false // missing flag counts as low
  return <Badge tone={low ? 'amber' : 'blue'}>{low ? 'Low confidence' : 'Confidence'} {Number(classification.confidence).toFixed(2)}</Badge>
}

export function StatusBadge({ status }) {
  const tone = { pending: 'gray', approved: 'green', rejected: 'red', escalated: 'amber' }[status] || 'gray'
  return <Badge tone={tone}>{status}</Badge>
}

export function Button({ variant = 'primary', className = '', ...props }) {
  const styles = {
    primary: 'btn-shine text-white disabled:opacity-50',
    secondary: 'bg-white/80 text-slate-700 shadow-sm ring-1 ring-inset ring-slate-300 hover:bg-white hover:shadow',
    danger: 'bg-white/80 text-rose-700 shadow-sm ring-1 ring-inset ring-rose-300 hover:bg-rose-50',
    warning: 'bg-white/80 text-amber-800 shadow-sm ring-1 ring-inset ring-amber-300 hover:bg-amber-50',
  }
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2 disabled:cursor-not-allowed ${styles[variant]} ${className}`}
      {...props}
    />
  )
}

export function Field({ label, hint, children }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-slate-700">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-slate-500">{hint}</span>}
    </label>
  )
}

export const inputClass =
  'block w-full rounded-xl border border-white/80 bg-white/75 px-3 py-2 text-sm shadow-[inset_0_1px_2px_rgb(15_23_42/0.08)] placeholder:text-slate-400 focus:border-indigo-400 focus:bg-white focus:ring-4 focus:ring-indigo-200/60 focus:outline-none'

export function ErrorBox({ error }) {
  if (!error) return null
  return <div role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</div>
}

export function Empty({ children }) {
  return <div className="rounded-xl border border-dashed border-indigo-200 bg-white/40 p-8 text-center text-sm text-slate-500">{children}</div>
}

// Shows a draft with citation tags like [KB-07 §2] highlighted.
export function DraftText({ text }) {
  const parts = text.split(/(\[KB-\d{2} §\d+\])/g)
  return (
    <p className="whitespace-pre-wrap text-sm leading-6 text-slate-800">
      {parts.map((p, i) =>
        /^\[KB-/.test(p) ? (
          <span key={i} className="mx-0.5 rounded-md bg-gradient-to-b from-indigo-50 to-indigo-100 px-1 font-mono text-xs text-indigo-700 ring-1 ring-indigo-200">{p.slice(1, -1)}</span>
        ) : (
          <span key={i}>{p}</span>
        ),
      )}
    </p>
  )
}

export function Evidence({ items }) {
  if (!items?.length) return <Empty>No sources retrieved.</Empty>
  return (
    <ul className="space-y-3">
      {items.map((e) => (
        <li key={e.chunk_id} className="rounded-xl border border-white/80 bg-white/60 p-3 shadow-sm">
          <div className="mb-1 flex items-center justify-between gap-2">
            <span className="font-mono text-xs font-semibold text-indigo-700">{e.chunk_id}</span>
            <span className="text-xs text-slate-500">match {e.score.toFixed(2)}</span>
          </div>
          <div className="text-xs font-medium text-slate-700">{e.title}</div>
          <p className="mt-1 text-xs leading-5 text-slate-600">{e.text}</p>
        </li>
      ))}
    </ul>
  )
}

export function Reasons({ reasons }) {
  if (!reasons?.length)
    return <div className="rounded-xl bg-gradient-to-r from-indigo-50 to-sky-50 px-4 py-3 text-sm text-indigo-800 ring-1 ring-indigo-100">All routing rules clear: standard review.</div>
  return (
    <div className="rounded-xl border border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50 px-4 py-3 shadow-sm">
      <div className="mb-1 text-sm font-semibold text-amber-900">Why this needs priority review</div>
      <ul className="list-disc space-y-0.5 pl-5 text-sm text-amber-900">
        {reasons.map((r) => <li key={r}>{r}</li>)}
      </ul>
    </div>
  )
}
