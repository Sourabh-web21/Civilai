import { motion, AnimatePresence } from 'framer-motion'
import { X } from 'lucide-react'

export default function Modal({ open, onClose, title, subtitle, children, width = 'max-w-lg' }) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 grid place-items-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div className="absolute inset-0 bg-slate-900/35 backdrop-blur-sm" onClick={onClose} />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: 10 }}
            transition={{ type: 'spring', damping: 22, stiffness: 260 }}
            className={`glass rounded-[28px] w-full ${width} relative z-10 max-h-[90vh] overflow-y-auto`}
          >
            <div className="flex items-start justify-between p-6 pb-2">
              <div>
                <h2 className="text-xl font-semibold font-display text-[#111827]">{title}</h2>
                {subtitle && <p className="text-sm text-[#6B7280] mt-0.5">{subtitle}</p>}
              </div>
              <button
                onClick={onClose}
                className="grid place-items-center h-10 w-10 rounded-full bg-slate-50 hover:bg-orange-50 hover:text-[#F97316] text-slate-500 transition"
              >
                <X size={18} />
              </button>
            </div>
            <div className="p-6 pt-2">{children}</div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
