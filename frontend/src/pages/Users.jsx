import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Plus, Users as UsersIcon, Mail, Phone, Shield, Loader2, AlertCircle, ListChecks } from 'lucide-react'
import { api, unwrap, errMessage } from '../api/client'
import { PageWrap, Loader, EmptyState } from '../components/ui'
import Modal from '../components/Modal'

const EMPTY = { first_name: '', last_name: '', email: '', phone: '', role: 'manager', password: '' }
const ROLE_COLORS = { admin: '#EF4444', manager: '#F97316', client: '#111827' }

export default function Users() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)

  const load = () => {
    setLoading(true)
    api.get('/api/v1/user/list')
      .then((res) => setUsers(unwrap(res) || []))
      .finally(() => setLoading(false))
  }
  useEffect(load, [])

  const name = (u) => u.full_name || [u.first_name, u.last_name].filter(Boolean).join(' ') || u.email?.split('@')[0]
  const initials = (u) => name(u).split(' ').map((s) => s[0]).slice(0, 2).join('').toUpperCase()

  return (
    <PageWrap>
      <div className="flex items-end justify-between gap-4 mb-6">
        <div>
          <h1 className="font-display text-3xl font-bold text-[#111827]">Team</h1>
          <p className="text-[#6B7280] mt-1">{users.length} members</p>
        </div>
        <button className="btn btn-primary" onClick={() => setOpen(true)}>
          <Plus size={18} /> Add User
        </button>
      </div>

      {loading ? (
        <Loader label="Loading team" />
      ) : users.length === 0 ? (
        <EmptyState icon={UsersIcon} title="No users yet" hint="Add managers, engineers or clients to your team."
          action={<button className="btn btn-primary mt-2" onClick={() => setOpen(true)}><Plus size={18} /> Add User</button>} />
      ) : (
        <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {users.map((u, i) => (
            <motion.div key={u.id} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
              className="glass glass-hover rounded-[24px] p-5">
              <div className="flex items-center gap-3">
                <div className="grid place-items-center h-12 w-12 rounded-2xl text-white font-semibold"
                  style={{ background: ROLE_COLORS[u.role] || '#111827' }}>
                  {initials(u)}
                </div>
                <div className="min-w-0">
                  <div className="font-medium text-[#111827] truncate">{name(u)}</div>
                  <div className="flex items-center gap-1 text-xs" style={{ color: ROLE_COLORS[u.role] || '#94a3b8' }}>
                    <Shield size={12} /> {u.role || 'member'}
                  </div>
                </div>
              </div>
              <div className="mt-4 space-y-2 text-sm text-[#6B7280]">
                <div className="flex items-center gap-2 truncate"><Mail size={14} className="shrink-0" /> {u.email}</div>
                <div className="flex items-center gap-2"><Phone size={14} /> {u.phone || '—'}</div>
                <div className="flex items-center gap-2"><ListChecks size={14} /> {u.total_tasks ?? 0} tasks assigned</div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      <UserModal open={open} onClose={() => setOpen(false)} onSaved={() => { setOpen(false); load() }} />
    </PageWrap>
  )
}

function UserModal({ open, onClose, onSaved }) {
  const [form, setForm] = useState(EMPTY)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      await api.post('/api/v1/user/list', form)
      setForm(EMPTY)
      onSaved()
    } catch (err) {
      setError(errMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Add User" subtitle="Invite a team member">
      <form onSubmit={submit} className="space-y-4">
        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label className="label">First name</label>
            <input className="field" value={form.first_name} onChange={set('first_name')} placeholder="Anil" />
          </div>
          <div>
            <label className="label">Last name</label>
            <input className="field" value={form.last_name} onChange={set('last_name')} placeholder="Kumar" />
          </div>
        </div>
        <div>
          <label className="label">Email <span className="text-[#F97316]">*</span></label>
          <input type="email" className="field" required value={form.email} onChange={set('email')} placeholder="anil@company.com" />
        </div>
        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Phone</label>
            <input className="field" value={form.phone} onChange={set('phone')} placeholder="9876543210" maxLength={10} />
          </div>
          <div>
            <label className="label">Role</label>
            <select className="field" value={form.role} onChange={set('role')}>
              <option value="admin">Admin</option>
              <option value="manager">Manager</option>
              <option value="client">Client</option>
            </select>
          </div>
        </div>
        <div>
          <label className="label">Password <span className="text-[#F97316]">*</span></label>
          <input type="password" className="field" required minLength={6} value={form.password} onChange={set('password')} placeholder="Min 6 characters" />
        </div>

        {error && (
          <div className="flex items-start gap-2 text-sm text-rose-300 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">
            <AlertCircle size={16} className="mt-0.5 shrink-0" /> {error}
          </div>
        )}

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button type="submit" disabled={saving} className="btn btn-primary">
            {saving ? <Loader2 size={18} className="animate-spin" /> : <><Plus size={18} /> Add User</>}
          </button>
        </div>
      </form>
    </Modal>
  )
}
