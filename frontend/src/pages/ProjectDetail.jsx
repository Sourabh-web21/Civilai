import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowLeft, Building2, Ruler, Calendar, IndianRupee, Clock,
  Trash2, ListChecks, Layers, Loader2,
} from 'lucide-react'
import { api, unwrap, errMessage } from '../api/client'
import { PageWrap, Loader, StatusChip, PriorityChip, EmptyState } from '../components/ui'
import ProgressRing from '../components/ProgressRing'

export default function ProjectDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    api
      .get(`/api/v1/project/list/${id}`)
      .then((res) => setProject(unwrap(res)))
      .catch(() => setProject(null))
      .finally(() => setLoading(false))
  }, [id])

  const remove = async () => {
    if (!confirm('Delete this project? This cannot be undone.')) return
    setDeleting(true)
    try {
      await api.delete(`/api/v1/project/list/${id}`)
      navigate('/projects')
    } catch (err) {
      alert(errMessage(err))
      setDeleting(false)
    }
  }

  if (loading) return <Loader label="Loading project" />
  if (!project) return <EmptyState icon={Layers} title="Project not found" hint="It may have been deleted." action={<Link to="/projects" className="btn btn-ghost mt-2">Back to projects</Link>} />

  const fmtDate = (d) => (d ? new Date(d).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' }) : '—')

  return (
    <PageWrap>
      <div className="flex items-center justify-between gap-4 mb-6">
        <button onClick={() => navigate('/projects')} className="btn btn-ghost">
          <ArrowLeft size={18} /> Back
        </button>
        <button onClick={remove} disabled={deleting} className="btn bg-rose-500/15 text-rose-300 hover:bg-rose-500/25">
          {deleting ? <Loader2 size={18} className="animate-spin" /> : <Trash2 size={18} />} Delete
        </button>
      </div>

      {/* Hero */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="glass rounded-[28px] p-6 md:p-8 relative overflow-hidden">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="font-display text-3xl font-bold text-[#111827]">{project.name}</h1>
              <StatusChip status={project.status} />
            </div>
            <p className="text-slate-400 mt-2">{project.state || 'Location N/A'} · {project.lane_configuration}</p>
          </div>
          <div className="flex gap-6">
            <ProgressRing value={Number(project.physical_progress) || 0} label="Physical" color="#F97316" />
            <ProgressRing value={Number(project.financial_progress) || 0} label="Financial" color="#FACC15" />
          </div>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
          <Info icon={Building2} label="Contractor" value={project.contractor_name} />
          <Info icon={Ruler} label="Length" value={`${project.length_km} km`} />
          <Info icon={IndianRupee} label="Total Cost" value={`₹${project.total_project_cost} Cr`} />
          <Info icon={IndianRupee} label="Tender Amount" value={`₹${project.tender_amount} Cr`} />
          <Info icon={Calendar} label="Sanctioned" value={fmtDate(project.sanction_date)} />
          <Info icon={Calendar} label="Appointed" value={fmtDate(project.appointed_date)} />
          <Info icon={Calendar} label="Scheduled Completion" value={fmtDate(project.scheduled_completion_date)} />
          <Info icon={Clock} label="Delay" value={`${project.total_delay_days || 0} days`} accent={project.total_delay_days > 0 ? '#f43f5e' : '#34d399'} />
        </div>
      </motion.div>

      {/* Tasks */}
      <div className="mt-6">
        <div className="flex items-center gap-2 mb-4">
          <ListChecks size={20} className="text-[#F97316]" />
          <h2 className="font-display text-xl font-semibold text-[#111827]">Tasks</h2>
          <span className="text-sm text-[#6B7280]">({project.tasks?.length || 0})</span>
        </div>

        {!project.tasks?.length ? (
          <div className="glass rounded-[24px] p-8 text-center text-[#6B7280]">No tasks linked to this project yet.</div>
        ) : (
          <div className="grid md:grid-cols-2 gap-3">
            {project.tasks.map((t, i) => (
              <motion.div
                key={t.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                className="glass glass-hover rounded-[24px] p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <h4 className="font-medium text-[#111827]">{t.title}</h4>
                  <PriorityChip priority={t.priority} />
                </div>
                {t.description && <p className="text-sm text-slate-400 mt-1 line-clamp-2">{t.description}</p>}
                <div className="flex items-center justify-between mt-3">
                  <StatusChip status={t.status} />
                  <span className="text-xs text-slate-500">
                    {t.assigned_to ? (t.assigned_to.full_name || t.assigned_to.email) : 'Unassigned'}
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </PageWrap>
  )
}

function Info({ icon: Icon, label, value, accent = '#94a3b8' }) {
  return (
    <div className="flex items-center gap-3">
      <div className="grid place-items-center h-10 w-10 rounded-2xl bg-slate-50 shrink-0" style={{ color: accent }}>
        <Icon size={18} />
      </div>
      <div className="min-w-0">
        <div className="text-[10px] uppercase tracking-wider text-[#6B7280]">{label}</div>
        <div className="text-[#111827] font-medium truncate">{value || '-'}</div>
      </div>
    </div>
  )
}
