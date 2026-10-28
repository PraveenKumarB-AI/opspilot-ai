// Small shared building blocks so every page looks consistent.

export function Card({ title, action, children, className = '' }) {
  return (
    <section className={`rounded-xl border border-slate-200 bg-white shadow-sm ${className}`}>
      {title && (
        <header className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
          <h2 className="text-sm font-semibold text-slate-700">{title}</h2>
          {action}
        </header>
      )}
      <div className="p-5">{children}</div>
    </section>
  )
}

const TONES = {
  gray: 'bg-slate-100 text-slate-700 ring-slate-200',
  blue: 'bg-indigo-50 text-indigo-700 ring-indigo-200',
  green: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  amber: 'bg-amber-50 text-amber-800 ring-amber-200',
  red: 'bg-rose-50 text-rose-700 ring-rose-200',
}

export function Badge({ tone = 'gray', children }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${TONES[tone]}`}>
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
    primary: 'bg-indigo-600 text-white hover:bg-indigo-700 disabled:bg-indigo-300',
    secondary: 'bg-white text-slate-700 ring-1 ring-inset ring-slate-300 hover:bg-slate-50',
    danger: 'bg-white text-rose-700 ring-1 ring-inset ring-rose-300 hover:bg-rose-50',
    warning: 'bg-white text-amber-800 ring-1 ring-inset ring-amber-300 hover:bg-amber-50',
  }
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition disabled:cursor-not-allowed ${styles[variant]} ${className}`}
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
  'block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm placeholder:text-slate-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none'

export function ErrorBox({ error }) {
  if (!error) return null
  return <div role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</div>
}

export function Empty({ children }) {
  return <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">{children}</div>
}

// Shows a draft with citation tags like [KB-07 §2] highlighted.
export function DraftText({ text }) {
  const parts = text.split(/(\[KB-\d{2} §\d+\])/g)
  return (
    <p className="whitespace-pre-wrap text-sm leading-6 text-slate-800">
      {parts.map((p, i) =>
        /^\[KB-/.test(p) ? (
          <span key={i} className="mx-0.5 rounded bg-indigo-50 px-1 font-mono text-xs text-indigo-700">{p.slice(1, -1)}</span>
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
        <li key={e.chunk_id} className="rounded-lg border border-slate-200 p-3">
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
    return <div className="rounded-lg bg-indigo-50 px-4 py-3 text-sm text-indigo-800">All routing rules clear: standard review.</div>
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
      <div className="mb-1 text-sm font-semibold text-amber-900">Why this needs priority review</div>
      <ul className="list-disc space-y-0.5 pl-5 text-sm text-amber-900">
        {reasons.map((r) => <li key={r}>{r}</li>)}
      </ul>
    </div>
  )
}
