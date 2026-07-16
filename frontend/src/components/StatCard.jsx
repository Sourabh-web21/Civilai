import { useEffect, useState } from 'react'
import { motion, useMotionValue, animate } from 'framer-motion'

function useCountUp(target = 0) {
  const mv = useMotionValue(0)
  const [val, setVal] = useState(0)
  useEffect(() => {
    const controls = animate(mv, target, {
      duration: 1.1,
      ease: 'easeOut',
      onUpdate: (v) => setVal(Math.round(v)),
    })
    return controls.stop
  }, [target]) // eslint-disable-line
  return val
}

export default function StatCard({ icon: Icon, label, value, accent = '#F97316', delay = 0 }) {
  const display = useCountUp(value)
  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5 }}
      whileHover={{ y: -4 }}
      className="glass glass-hover rounded-[24px] p-6 relative overflow-hidden"
    >
      <div
        className="absolute -right-8 -top-8 h-28 w-28 rounded-full opacity-10"
        style={{ background: accent }}
      />
      <div className="flex items-center justify-between">
        <div
          className="grid place-items-center h-12 w-12 rounded-2xl"
          style={{ background: `${accent}18`, color: accent }}
        >
          {Icon && <Icon size={20} />}
        </div>
      </div>
      <div className="mt-4">
        <div className="text-3xl font-bold font-display text-[#111827]">{display}</div>
        <div className="text-sm text-[#6B7280] mt-0.5">{label}</div>
      </div>
    </motion.div>
  )
}
