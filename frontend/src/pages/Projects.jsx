import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Plus, MapPin, Building2, Ruler, FolderKanban, Loader2, AlertCircle } from 'lucide-react'
import { api, unwrap, errMessage } from '../api/client'
import { PageWrap, Loader, EmptyState, StatusChip } from '../components/ui'
import ProgressRing from '../components/ProgressRing'
import Modal from '../components/Modal'

const EMPTY = {
  name: '', state: '', contractor_name: '', lane_configuration: '2 lane',
  length_km: '', total_project_cost: '', tender_amount: '',
  completion_period_months: '', total_delay_days: 0,
  physical_progress: 0, financial_progress: 0, status: 'planning',
  sanction_date: '', appointed_date: '', scheduled_completion_date: '',
}

export default function Projects() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)

  const load = () => {
    setLoading(true)
    api
      .get('/api/v1/project/list')
      .then((res) => setProjects(unwrap(res) || []))
      .finally(() => setLoading(false))
  }
  useEffect(load, [])

  return (
    <PageWrap>
      <div className="flex items-end justify-between gap-4 mb-6">
        <div>
          <h1 className="font-display text-3xl font-bold text-[#111827]">Projects</h1>
          <p className="text-[#6B7280] mt-1">{projects.length} construction projects under management</p>
        </div>
        <button className="btn btn-primary" onClick={() => setOpen(true)}>
          <Plus size={18} /> New Project
        </button>
      </div>

      {loading ? (
        <Loader label="Loading projects" />
      ) : projects.length === 0 ? (
        <EmptyState
          icon={FolderKanban}
          title="No projects yet"
          hint="Create your first highway or road project to start tracking progress."
          action={<button className="btn btn-primary mt-2" onClick={() => setOpen(true)}><Plus size={18} /> New Project</button>}
        />
      ) : (
        <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {projects.map((p, i) => (
            <motion.div
              key={p.id}
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <Link to={`/projects/${p.id}`}>
                <div className="glass glass-hover rounded-[24px] p-5 h-full">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h3 className="font-display font-semibold text-lg text-[#111827] truncate">{p.name}</h3>
                      <div className="flex items-center gap-1.5 text-sm text-[#6B7280] mt-1">
                        <MapPin size={14} /> {p.state || 'Location N/A'}
                      </div>
                    </div>
                    <ProgressRing value={Number(p.physical_progress) || 0} size={64} stroke={6} label="built" />
                  </div>

                  <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                    <Meta icon={Building2} label="Contractor" value={p.contractor_name} />
                    <Meta icon={Ruler} label="Length" value={`${p.length_km} km`} />
                  </div>

                  <div className="mt-4 flex items-center justify-between">
                    <StatusChip status={p.status} />
                    <span className="text-xs text-[#6B7280]">{p.tasks?.length || 0} tasks</span>
                  </div>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      )}

      <ProjectModal open={open} onClose={() => setOpen(false)} onSaved={() => { setOpen(false); load() }} />
    </PageWrap>
  )
}

function Meta({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center gap-2 min-w-0">
      <Icon size={15} className="text-[#6B7280] shrink-0" />
      <div className="min-w-0">
        <div className="text-[10px] uppercase tracking-wider text-[#6B7280]">{label}</div>
        <div className="text-[#111827] truncate">{value || '-'}</div>
      </div>
    </div>
  )
}

function ProjectModal({ open, onClose, onSaved }) {
  const [form, setForm] = useState(EMPTY)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      const payload = {
        ...form,
        length_km: Number(form.length_km),
        total_project_cost: Number(form.total_project_cost),
        tender_amount: Number(form.tender_amount),
        completion_period_months: Number(form.completion_period_months),
        total_delay_days: Number(form.total_delay_days) || 0,
        physical_progress: Number(form.physical_progress),
        financial_progress: Number(form.financial_progress),
      }
      await api.post('/api/v1/project/list', payload)
      setForm(EMPTY)
      onSaved()
    } catch (err) {
      setError(errMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="New Project" subtitle="Add a highway / road project" width="max-w-2xl">
      <form onSubmit={submit} className="space-y-4">
        <div className="grid sm:grid-cols-2 gap-4">
          <Field label="Project name" required value={form.name} onChange={set('name')} placeholder="NH-30 Widening" />
          <Field label="State / Location" value={form.state} onChange={set('state')} placeholder="Maharashtra" />
          <Field label="Contractor" required value={form.contractor_name} onChange={set('contractor_name')} placeholder="NTPC" />
          <Field label="Lane configuration" required value={form.lane_configuration} onChange={set('lane_configuration')} placeholder="2 lane" />
          <Field label="Length (km)" required type="number" step="0.01" value={form.length_km} onChange={set('length_km')} />
          <Field label="Total cost (Cr)" required type="number" step="0.01" value={form.total_project_cost} onChange={set('total_project_cost')} />
          <Field label="Tender amount (Cr)" required type="number" step="0.01" value={form.tender_amount} onChange={set('tender_amount')} />
          <Field label="Completion (months)" required type="number" value={form.completion_period_months} onChange={set('completion_period_months')} />
          <Field label="Sanction date" required type="date" value={form.sanction_date} onChange={set('sanction_date')} />
          <Field label="Appointed date" required type="date" value={form.appointed_date} onChange={set('appointed_date')} />
          <Field label="Scheduled completion" required type="date" value={form.scheduled_completion_date} onChange={set('scheduled_completion_date')} />
          <div>
            <label className="label">Status</label>
            <select className="field" value={form.status} onChange={set('status')}>
              <option value="planning">Planning</option>
              <option value="on going">On Going</option>
              <option value="on hold">On Hold</option>
              <option value="completed">Completed</option>
            </select>
          </div>
          <Field label="Physical progress (%)" type="number" min="0" max="100" value={form.physical_progress} onChange={set('physical_progress')} />
          <Field label="Financial progress (%)" type="number" min="0" max="100" value={form.financial_progress} onChange={set('financial_progress')} />
        </div>

        {error && (
          <div className="flex items-start gap-2 text-sm text-rose-300 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">
            <AlertCircle size={16} className="mt-0.5 shrink-0" /> {error}
          </div>
        )}

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button type="submit" disabled={saving} className="btn btn-primary">
            {saving ? <Loader2 size={18} className="animate-spin" /> : <><Plus size={18} /> Create Project</>}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function Field({ label, required, ...props }) {
  return (
    <div>
      <label className="label">{label}{required && <span className="text-[#F97316]"> *</span>}</label>
      <input className="field" required={required} {...props} />
    </div>
  )
}
