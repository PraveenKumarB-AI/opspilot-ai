export default function PageHeader({ title, subtitle, children }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="bg-gradient-to-r from-slate-900 via-indigo-800 to-violet-700 bg-clip-text text-3xl font-bold tracking-tight text-transparent">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-600">{subtitle}</p>}
      </div>
      {children}
    </div>
  )
}
