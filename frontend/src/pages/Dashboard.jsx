import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  FolderKanban, ListChecks, Clock, CheckCircle2, PauseCircle, Activity,
} from 'lucide-react'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
  PieChart, Pie, Cell,
} from 'recharts'
import { api, unwrap } from '../api/client'
import { useAuth } from '../context/AuthContext'
import StatCard from '../components/StatCard'
import { PageWrap, Loader } from '../components/ui'

const COLORS = ['#F97316', '#FACC15', '#EF4444', '#22C55E']

export default function Dashboard() {
  const { user } = useAuth()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get('/api/v1/project/dashboard')
      .then((res) => setData(unwrap(res)))
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Loader label="Loading dashboard" />

  const projects = data?.projects || { total: 0, new: 0, ongoing: 0, on_hold: 0, completed: 0 }
  const tasks = data?.tasks || { total: 0, new: 0, ongoing: 0, on_hold: 0, completed: 0 }

  const breakdown = (d) => [
    { name: 'Planning', value: d.new },
    { name: 'On Going', value: d.ongoing },
    { name: 'On Hold', value: d.on_hold },
    { name: 'Completed', value: d.completed },
  ]

  const barData = [
    { name: 'Planning', Projects: projects.new, Tasks: tasks.new },
    { name: 'On Going', Projects: projects.ongoing, Tasks: tasks.ongoing },
    { name: 'On Hold', Projects: projects.on_hold, Tasks: tasks.on_hold },
    { name: 'Completed', Projects: projects.completed, Tasks: tasks.completed },
  ]

  return (
    <PageWrap>
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold text-[#111827]">
            Welcome back, {user?.full_name?.split(' ')[0] || 'Admin'}
          </h1>
          <p className="mt-1 text-[#6B7280]">Here's what's happening across your projects.</p>
        </div>
        <div className="glass flex items-center gap-2 rounded-full px-4 py-2 text-sm text-[#6B7280]">
          <Activity size={16} className="text-[#22C55E]" />
          Live · {projects.total} projects tracked
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard icon={FolderKanban} label="Total Projects" value={projects.total} accent="#F97316" delay={0} />
        <StatCard icon={Activity} label="Ongoing Projects" value={projects.ongoing} accent="#FACC15" delay={0.08} />
        <StatCard icon={ListChecks} label="Total Tasks" value={tasks.total} accent="#111827" delay={0.16} />
        <StatCard icon={CheckCircle2} label="Completed Tasks" value={tasks.completed} accent="#22C55E" delay={0.24} />
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass rounded-[28px] p-6 lg:col-span-2"
        >
          <h3 className="font-display mb-1 text-lg font-semibold text-[#111827]">Projects vs Tasks</h3>
          <p className="mb-4 text-sm text-[#6B7280]">Distribution by status</p>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
              <XAxis dataKey="name" stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} allowDecimals={false} />
              <Tooltip
                cursor={{ fill: '#FFF7ED' }}
                contentStyle={{
                  background: '#FFFFFF',
                  border: '1px solid #E5E7EB',
                  borderRadius: 16,
                  boxShadow: '0 16px 40px rgba(17,24,39,0.08)',
                }}
              />
              <Bar dataKey="Projects" radius={[10, 10, 0, 0]} fill="#F97316" />
              <Bar dataKey="Tasks" radius={[10, 10, 0, 0]} fill="#FACC15" />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.38 }}
          className="glass rounded-[28px] p-6"
        >
          <h3 className="font-display mb-1 text-lg font-semibold text-[#111827]">Project Mix</h3>
          <p className="mb-2 text-sm text-[#6B7280]">By current status</p>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={breakdown(projects)}
                dataKey="value"
                nameKey="name"
                innerRadius={55}
                outerRadius={85}
                paddingAngle={3}
                stroke="none"
              >
                {breakdown(projects).map((_, i) => (
                  <Cell key={i} fill={COLORS[i]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: '#FFFFFF',
                  border: '1px solid #E5E7EB',
                  borderRadius: 16,
                  boxShadow: '0 16px 40px rgba(17,24,39,0.08)',
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-2 grid grid-cols-2 gap-2">
            {breakdown(projects).map((b, i) => (
              <div key={b.name} className="flex items-center gap-2 text-xs text-[#6B7280]">
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: COLORS[i] }} />
                {b.name} · <span className="font-medium text-[#111827]">{b.value}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MiniStat icon={Clock} label="Planning" value={projects.new} color="#F97316" />
        <MiniStat icon={Activity} label="On Going" value={projects.ongoing} color="#FACC15" />
        <MiniStat icon={PauseCircle} label="On Hold" value={projects.on_hold} color="#EF4444" />
        <MiniStat icon={CheckCircle2} label="Completed" value={projects.completed} color="#22C55E" />
      </div>
    </PageWrap>
  )
}

function MiniStat({ icon: Icon, label, value, color }) {
  return (
    <div className="glass glass-hover flex items-center gap-3 rounded-[24px] p-4">
      <div className="grid h-10 w-10 place-items-center rounded-2xl" style={{ background: `${color}18`, color }}>
        <Icon size={18} />
      </div>
      <div>
        <div className="text-xl font-bold text-[#111827]">{value}</div>
        <div className="text-xs text-[#6B7280]">{label}</div>
      </div>
    </div>
  )
}
