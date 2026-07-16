import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Save, Loader2, AlertCircle, CheckCircle2, KeyRound, LogOut } from 'lucide-react'
import { api, unwrap, errMessage } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import { PageWrap, Loader } from '../components/ui'

export default function Profile() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState(null)

  // password card
  const [pw, setPw] = useState({ old_password: '', new_password: '' })
  const [pwMsg, setPwMsg] = useState(null)
  const [pwSaving, setPwSaving] = useState(false)

  useEffect(() => {
    api.get('/api/v1/user/profile')
      .then((res) => setForm(unwrap(res) || {}))
      .catch(() => setForm({ email: user?.email, full_name: user?.full_name }))
      .finally(() => setLoading(false))
  }, []) // eslint-disable-line

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const save = async (e) => {
    e.preventDefault()
    setMsg(null); setSaving(true)
    try {
      await api.patch('/api/v1/user/profile', {
        first_name: form.first_name, last_name: form.last_name,
        phone: form.phone, username: form.username,
      })
      setMsg({ ok: true, text: 'Profile updated' })
    } catch (err) {
      setMsg({ ok: false, text: errMessage(err) })
    } finally { setSaving(false) }
  }

  const changePw = async (e) => {
    e.preventDefault()
    setPwMsg(null); setPwSaving(true)
    try {
      await api.post('/api/v1/user/change-password', pw)
      setPwMsg({ ok: true, text: 'Password changed' })
      setPw({ old_password: '', new_password: '' })
    } catch (err) {
      setPwMsg({ ok: false, text: errMessage(err) })
    } finally { setPwSaving(false) }
  }

  if (loading) return <Loader label="Loading profile" />

  const initials = (form?.full_name || form?.email || user?.email || 'A')
    .split(' ').map((s) => s[0]).slice(0, 2).join('').toUpperCase()

  return (
    <PageWrap>
      <h1 className="font-display text-3xl font-bold text-[#111827] mb-6">Profile</h1>

      <div className="grid lg:grid-cols-3 gap-4">
        {/* Identity card */}
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="glass rounded-[28px] p-6 flex flex-col items-center text-center">
          <div className="grid place-items-center h-24 w-24 rounded-[28px] bg-[#111827] text-white text-3xl font-bold">
            {initials}
          </div>
          <h2 className="font-display text-xl font-semibold text-[#111827] mt-4">{form?.full_name || `${form?.first_name || ''} ${form?.last_name || ''}`.trim() || 'Admin'}</h2>
          <p className="text-[#6B7280] text-sm">{form?.email}</p>
          <button onClick={() => { logout(); navigate('/login') }} className="btn btn-ghost mt-6 w-full">
            <LogOut size={18} /> Sign out
          </button>
        </motion.div>

        {/* Edit form */}
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 }} className="glass rounded-[28px] p-6 lg:col-span-2">
          <h3 className="font-display font-semibold text-lg text-[#111827] mb-4">Account details</h3>
          <form onSubmit={save} className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="label">First name</label>
              <input className="field" value={form?.first_name || ''} onChange={set('first_name')} />
            </div>
            <div>
              <label className="label">Last name</label>
              <input className="field" value={form?.last_name || ''} onChange={set('last_name')} />
            </div>
            <div>
              <label className="label">Username</label>
              <input className="field" value={form?.username || ''} onChange={set('username')} />
            </div>
            <div>
              <label className="label">Phone</label>
              <input className="field" value={form?.phone || ''} onChange={set('phone')} maxLength={10} />
            </div>
            <div className="sm:col-span-2">
              <label className="label">Email (read only)</label>
              <input className="field opacity-60 cursor-not-allowed" value={form?.email || ''} readOnly />
            </div>

            {msg && (
              <div className={`sm:col-span-2 flex items-center gap-2 text-sm rounded-lg px-3 py-2 ${msg.ok ? 'text-emerald-300 bg-emerald-500/10' : 'text-rose-300 bg-rose-500/10'}`}>
                {msg.ok ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />} {msg.text}
              </div>
            )}

            <div className="sm:col-span-2 flex justify-end">
              <button type="submit" disabled={saving} className="btn btn-primary">
                {saving ? <Loader2 size={18} className="animate-spin" /> : <><Save size={18} /> Save changes</>}
              </button>
            </div>
          </form>
        </motion.div>

        {/* Password */}
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.16 }} className="glass rounded-[28px] p-6 lg:col-span-3">
          <h3 className="font-display font-semibold text-lg text-[#111827] mb-4 flex items-center gap-2">
            <KeyRound size={18} className="text-[#F97316]" /> Change password
          </h3>
          <form onSubmit={changePw} className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="label">Current password</label>
              <input type="password" className="field" required value={pw.old_password} onChange={(e) => setPw((p) => ({ ...p, old_password: e.target.value }))} />
            </div>
            <div>
              <label className="label">New password</label>
              <input type="password" className="field" required minLength={6} value={pw.new_password} onChange={(e) => setPw((p) => ({ ...p, new_password: e.target.value }))} />
            </div>
            {pwMsg && (
              <div className={`sm:col-span-2 flex items-center gap-2 text-sm rounded-lg px-3 py-2 ${pwMsg.ok ? 'text-emerald-300 bg-emerald-500/10' : 'text-rose-300 bg-rose-500/10'}`}>
                {pwMsg.ok ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />} {pwMsg.text}
              </div>
            )}
            <div className="sm:col-span-2 flex justify-end">
              <button type="submit" disabled={pwSaving} className="btn btn-primary">
                {pwSaving ? <Loader2 size={18} className="animate-spin" /> : <><KeyRound size={18} /> Update password</>}
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </PageWrap>
  )
}
