import { motion } from 'framer-motion'

export function PageWrap({ children }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  )
}

export function Loader({ label = 'Loading' }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-24 text-slate-500">
      <div className="relative h-12 w-12">
        <div className="absolute inset-0 rounded-full border-2 border-slate-200" />
        <motion.div
          className="absolute inset-0 rounded-full border-2 border-transparent border-t-[#F97316]"
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 0.9, ease: 'linear' }}
        />
      </div>
      <span className="text-sm tracking-wide">{label}…</span>
    </div>
  )
}

export function EmptyState({ icon: Icon, title, hint, action }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass rounded-[28px] flex flex-col items-center justify-center gap-3 py-20 text-center"
    >
      {Icon && (
        <div className="grid place-items-center h-14 w-14 rounded-2xl bg-orange-50 text-[#F97316]">
          <Icon size={26} />
        </div>
      )}
      <h3 className="text-lg font-semibold text-[#111827]">{title}</h3>
      {hint && <p className="text-sm text-[#6B7280] max-w-sm">{hint}</p>}
      {action}
    </motion.div>
  )
}

const STATUS = {
  planning: { cls: 'chip-planning', label: 'Planning' },
  'on going': { cls: 'chip-ongoing', label: 'On Going' },
  'on hold': { cls: 'chip-hold', label: 'On Hold' },
  completed: { cls: 'chip-completed', label: 'Completed' },
}
export function StatusChip({ status }) {
  const s = STATUS[status] || { cls: 'chip-planning', label: status || '—' }
  return <span className={`chip ${s.cls}`}><span className="h-1.5 w-1.5 rounded-full bg-current" />{s.label}</span>
}

const PRIORITY = {
  low: 'text-emerald-700 bg-emerald-50',
  medium: 'text-orange-700 bg-orange-50',
  high: 'text-red-700 bg-red-50',
}
export function PriorityChip({ priority }) {
  return (
    <span className={`chip ${PRIORITY[priority] || PRIORITY.medium}`}>
      {priority || 'medium'}
    </span>
  )
}
