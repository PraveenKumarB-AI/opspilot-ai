// The ticket journey: every stage a request passes through, left to right, ending in the outcome.
// It is the one place the whole decision can be read at a glance, so it leads every request view.

const STAGES = ['Received', 'Understood', 'Sources', 'Draft', 'Safety rules', 'Outcome']

const ACTION = { approve: 'Approved', edit: 'Edited and sent', reject: 'Draft rejected', escalate: 'Escalated' }

// Turn a request from the API into six stations: { title, detail, tone }.
// tone: ok (passed), warn (needs care), stop (blocked), sent (emailed), wait (with a person).
export function journeyOf(r) {
  const c = r.classification || {}
  const reasons = r.review?.routing_reasons || []
  const top = r.evidence?.[0]
  const weak = reasons.some((x) => x.startsWith('Weak evidence'))
  const d = r.draft || {}
  const action = r.review?.action

  let outcome
  if (action === 'auto_send') outcome = { title: 'Emailed automatically', detail: 'All 9 checks passed', tone: 'sent' }
  else if (action) outcome = { title: ACTION[action] || action, detail: `By ${r.review.reviewer}`, tone: action === 'reject' ? 'stop' : 'sent' }
  else outcome = { title: 'With a person', detail: r.review?.queue === 'priority' ? 'Priority review' : 'Standard review', tone: 'wait' }

  return [
    { title: `Via ${r.channel || 'web'}`, detail: `From ${r.customer}`, tone: 'ok' },
    { title: c.category ? `${c.category[0].toUpperCase()}${c.category.slice(1).replace('_', ' ')}` : 'Not classified',
      detail: `${c.risk === 'high' ? 'High' : 'Low'} risk, confidence ${Number(c.confidence ?? 0).toFixed(2)}`,
      tone: c.risk === 'high' || c.low_confidence ? 'warn' : 'ok' },
    { title: top ? top.chunk_id : 'Nothing found', detail: top ? `Best match ${Number(top.score).toFixed(2)}` : 'No article matched',
      tone: !top || weak ? 'warn' : 'ok' },
    d.mode === 'none' || !d.mode
      ? { title: 'Not written', detail: 'Unsafe to guess', tone: 'stop' }
      : d.mode === 'holding'
      ? { title: 'Holding reply', detail: 'No facts, so no guessing', tone: 'warn' }
      : { title: d.mode === 'llm' ? 'Written by the LLM' : 'Copied from sources',
          detail: d.citation_ok ? 'Citations verified' : 'Citation check failed', tone: d.citation_ok ? 'ok' : 'stop' },
    reasons.length
      ? { title: `${reasons.length} rule${reasons.length > 1 ? 's' : ''} fired`, detail: reasons[0].split(' (')[0], tone: 'warn' }
      : { title: 'All 7 clear', detail: 'Nothing risky found', tone: 'ok' },
    outcome,
  ]
}

const DOT = {
  ok: 'dot-ok', warn: 'dot-warn', stop: 'dot-stop', sent: 'dot-sent', wait: 'dot-wait', idle: 'dot-idle',
}

export default function Journey({ request }) {
  const stations = request ? journeyOf(request) : STAGES.map((s) => ({ title: s, detail: '', tone: 'idle' }))
  return (
    <ol key={request?.id ?? 'empty'} className="journey" aria-label="Ticket journey">
      {stations.map((s, i) => (
        <li key={i} className={`station ${i === stations.length - 1 ? 'station-end' : ''}`} style={{ '--i': i }}>
          <span className={`dot ${DOT[s.tone]}`} aria-hidden="true" />
          <div className="w-full min-w-0 overflow-hidden">
            <div className="text-[11px] font-medium text-slate-500">{STAGES[i]}</div>
            <div className="text-sm font-semibold leading-snug text-slate-900 [overflow-wrap:anywhere]">{request ? s.title : ''}</div>
            {s.detail && <div className="mt-0.5 text-xs leading-snug text-slate-600 [overflow-wrap:anywhere]">{s.detail}</div>}
          </div>
        </li>
      ))}
    </ol>
  )
}
