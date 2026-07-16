import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Plus, ListChecks, Loader2, AlertCircle, CalendarDays, User2 } from 'lucide-react'
import { api, unwrap, errMessage } from '../api/client'
import { PageWrap, Loader, EmptyState, StatusChip, PriorityChip } from '../components/ui'
import Modal from '../components/Modal'

const EMPTY = {
  title: '', description: '', priority: 'medium', status: 'planning',
  due_date: '', project: '', assigned_to_id: '',
}

export default function Tasks() {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const [filter, setFilter] = useState('all')

  const load = () => {
    setLoading(true)
    api.get('/api/v1/project/tasks/list')
      .then((res) => setTasks(unwrap(res) || []))
      .finally(() => setLoading(false))
  }
  useEffect(load, [])

  const filtered = filter === 'all' ? tasks : tasks.filter((t) => t.status === filter)
  const FILTERS = ['all', 'planning', 'on going', 'on hold', 'completed']

  return (
    <PageWrap>
      <div className="flex items-end justify-between gap-4 mb-6">
        <div>
          <h1 className="font-display text-3xl font-bold text-[#111827]">Tasks</h1>
          <p className="text-[#6B7280] mt-1">{tasks.length} tasks across all projects</p>
        </div>
        <button className="btn btn-primary" onClick={() => setOpen(true)}>
          <Plus size={18} /> New Task
        </button>
      </div>

      <div className="flex gap-2 mb-5 flex-wrap">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`chip capitalize transition ${
              filter === f ? 'bg-[#F97316] text-white font-semibold' : 'bg-white text-[#6B7280] border border-[#E5E7EB] hover:text-[#F97316]'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {loading ? (
        <Loader label="Loading tasks" />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={ListChecks}
          title={filter === 'all' ? 'No tasks yet' : `No ${filter} tasks`}
          hint="Create a task and assign it to a team member."
          action={<button className="btn btn-primary mt-2" onClick={() => setOpen(true)}><Plus size={18} /> New Task</button>}
        />
      ) : (
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((t, i) => (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
              className="glass glass-hover rounded-[24px] p-5"
            >
              <div className="flex items-start justify-between gap-3">
                <h3 className="font-medium text-[#111827]">{t.title}</h3>
                <PriorityChip priority={t.priority} />
              </div>
              {t.description && <p className="text-sm text-slate-400 mt-1.5 line-clamp-2">{t.description}</p>}
              {t.project_name && (
                <div className="mt-3 text-xs text-[#EA580C] bg-orange-50 inline-block px-2 py-1 rounded-full">
                  {t.project_name}
                </div>
              )}
              <div className="mt-4 flex items-center justify-between">
                <StatusChip status={t.status} />
                <div className="flex items-center gap-3 text-xs text-slate-500">
                  {t.due_date && <span className="flex items-center gap-1"><CalendarDays size={13} />{new Date(t.due_date).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })}</span>}
                  <span className="flex items-center gap-1"><User2 size={13} />{t.assigned_to ? (t.assigned_to.full_name || t.assigned_to.email?.split('@')[0]) : '—'}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      <TaskModal open={open} onClose={() => setOpen(false)} onSaved={() => { setOpen(false); load() }} />
    </PageWrap>
  )
}

function TaskModal({ open, onClose, onSaved }) {
  const [form, setForm] = useState(EMPTY)
  const [users, setUsers] = useState([])
  const [projects, setProjects] = useState([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open) return
    api.get('/api/v1/user/list').then((res) => setUsers(unwrap(res) || [])).catch(() => {})
    api.get('/api/v1/project/list').then((res) => setProjects(unwrap(res) || [])).catch(() => {})
  }, [open])

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      const payload = {
        title: form.title,
        description: form.description,
        priority: form.priority,
        status: form.status,
        assigned_to_id: form.assigned_to_id,
      }
      if (form.due_date) payload.due_date = form.due_date
      if (form.project) payload.project = form.project
      await api.post('/api/v1/project/tasks/list', payload)
      setForm(EMPTY)
      onSaved()
    } catch (err) {
      setError(errMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const userName = (u) => u.full_name || [u.first_name, u.last_name].filter(Boolean).join(' ') || u.email

  return (
    <Modal open={open} onClose={onClose} title="New Task" subtitle="Assign work to a team member">
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="label">Title <span className="text-[#F97316]">*</span></label>
          <input className="field" required value={form.title} onChange={set('title')} placeholder="Complete drainage on section 2" />
        </div>
        <div>
          <label className="label">Description</label>
          <textarea className="field min-h-[80px]" value={form.description} onChange={set('description')} placeholder="Details…" />
        </div>
        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Assign to <span className="text-[#F97316]">*</span></label>
            <select className="field" required value={form.assigned_to_id} onChange={set('assigned_to_id')}>
              <option value="">Select user…</option>
              {users.map((u) => <option key={u.id} value={u.id}>{userName(u)}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Project</label>
            <select className="field" value={form.project} onChange={set('project')}>
              <option value="">No project</option>
              {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Priority</label>
            <select className="field" value={form.priority} onChange={set('priority')}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
          <div>
            <label className="label">Status</label>
            <select className="field" value={form.status} onChange={set('status')}>
              <option value="planning">Planning</option>
              <option value="on going">On Going</option>
              <option value="on hold">On Hold</option>
              <option value="completed">Completed</option>
            </select>
          </div>
          <div className="sm:col-span-2">
            <label className="label">Due date</label>
            <input type="date" className="field" value={form.due_date} onChange={set('due_date')} />
          </div>
        </div>

        {error && (
          <div className="flex items-start gap-2 text-sm text-rose-300 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">
            <AlertCircle size={16} className="mt-0.5 shrink-0" /> {error}
          </div>
        )}
        {users.length === 0 && (
          <div className="text-xs text-amber-300/80">Tip: you need at least one user to assign a task. Add one on the Users page.</div>
        )}

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button type="submit" disabled={saving} className="btn btn-primary">
            {saving ? <Loader2 size={18} className="animate-spin" /> : <><Plus size={18} /> Create Task</>}
          </button>
        </div>
      </form>
    </Modal>
  )
}
