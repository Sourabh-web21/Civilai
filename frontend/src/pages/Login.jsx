import { useState } from 'react'
import { useNavigate, Navigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { HardHat, Mail, Lock, ArrowRight, Loader2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import SplineHero from '../components/SplineHero'

export default function Login() {
  const { login, isAuthed } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('admin@civil.ai')
  const [password, setPassword] = useState('admin12345')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (isAuthed) return <Navigate to="/" replace />

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    const res = await login(email, password)
    setLoading(false)
    if (res.ok) navigate('/')
    else setError(res.error)
  }

  return (
    <div className="aurora-bg grid min-h-screen lg:grid-cols-2">
      <div className="relative z-10 hidden min-h-screen flex-col justify-between overflow-hidden p-10 lg:flex xl:p-12">
        <div className="relative z-20 flex items-center gap-3">
          <div className="grid h-12 w-12 place-items-center rounded-2xl bg-[#F97316] text-white shadow-[0_12px_24px_rgba(249,115,22,0.24)]">
            <HardHat size={22} />
          </div>
          <span className="font-display text-xl font-bold text-[#111827]">CivilAI</span>
        </div>

        <div className="absolute -right-[6%] bottom-0 z-0 h-[82vh] max-h-[760px] min-h-[560px] w-[68%] overflow-hidden" aria-hidden="true">
          <SplineHero />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="relative z-10 max-w-[21rem] pb-2 xl:max-w-[24rem]"
        >
          <h1 className="font-display text-4xl font-bold leading-[1.12] text-[#111827] xl:text-5xl">
            Build smarter.
            <br />
            <span className="text-[#F97316]">Track every kilometer.</span>
          </h1>
          <p className="mt-5 text-base leading-7 text-[#6B7280]">
            Real-time intelligence for highway and road construction: projects, tasks,
            progress and AI-powered document search, all in one command center.
          </p>
        </motion.div>
      </div>

      <div className="relative z-10 flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="glass w-full max-w-md rounded-[28px] p-6 sm:p-8"
        >
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <div className="grid h-12 w-12 place-items-center rounded-2xl bg-[#F97316] text-white">
              <HardHat size={22} />
            </div>
            <span className="font-display text-xl font-bold text-[#111827]">CivilAI</span>
          </div>

          <h2 className="font-display text-2xl font-bold text-[#111827]">Welcome back</h2>
          <p className="mt-1 text-sm text-[#6B7280]">Sign in to your command center.</p>

          <form onSubmit={submit} className="mt-7 space-y-4">
            <div>
              <label className="label">Email</label>
              <div className="relative">
                <Mail size={18} className="absolute left-3.5 top-3.5 text-slate-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="field !pl-12"
                  placeholder="you@company.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="label">Password</label>
              <div className="relative">
                <Lock size={18} className="absolute left-3.5 top-3.5 text-slate-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="field !pl-12"
                  placeholder="Password"
                  required
                />
              </div>
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="rounded-2xl border border-red-100 bg-red-50 px-3 py-2 text-sm text-red-700"
              >
                {error}
              </motion.div>
            )}

            <button type="submit" disabled={loading} className="btn btn-primary w-full">
              {loading ? <Loader2 size={18} className="animate-spin" /> : <>Sign in <ArrowRight size={18} /></>}
            </button>
          </form>

          <div className="mt-6 text-center text-xs text-[#6B7280]">
            Demo credentials are pre-filled · <span className="font-medium text-[#111827]">admin@civil.ai</span>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
