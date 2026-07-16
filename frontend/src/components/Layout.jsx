import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard, FolderKanban, ListChecks, Users as UsersIcon,
  UserCircle, LogOut, HardHat, Bot, Search, Bell, PlugZap,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/chat', label: 'CivilAI Chat', icon: Bot },
  { to: '/ai-connect', label: 'AiConnect', icon: PlugZap },
  { to: '/projects', label: 'Projects', icon: FolderKanban },
  { to: '/tasks', label: 'Tasks', icon: ListChecks },
  { to: '/users', label: 'Users', icon: UsersIcon },
  { to: '/profile', label: 'Profile', icon: UserCircle },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const initials = (user?.full_name || user?.email || 'A')
    .split(' ')
    .map((s) => s[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

  return (
    <div className="aurora-bg min-h-screen">
      <div className="relative z-10 flex min-h-screen p-3 md:p-5 gap-5">
        {/* Sidebar */}
        <aside className="hidden md:flex w-72 shrink-0 flex-col rounded-[28px] bg-[#111827] p-4 text-white shadow-[0_24px_60px_rgba(17,24,39,0.18)]">
          <div className="flex items-center gap-3 px-2 py-3">
            <div className="grid place-items-center h-12 w-12 rounded-2xl bg-[#F97316] text-white shadow-[0_12px_24px_rgba(249,115,22,0.28)]">
              <HardHat size={22} />
            </div>
            <div>
              <div className="font-display font-bold text-xl leading-none text-white">CivilAI</div>
              <div className="text-[10px] uppercase tracking-widest text-slate-400 mt-1">
                Construction Intel
              </div>
            </div>
          </div>

          <nav className="mt-8 flex flex-col gap-2">
            {NAV.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.end}>
                {({ isActive }) => (
                  <motion.div
                    whileHover={{ x: 3 }}
                    className={`relative flex items-center gap-3 rounded-2xl px-3.5 py-3 text-sm font-semibold transition ${
                      isActive ? 'text-white' : 'text-slate-400 hover:bg-white/10 hover:text-white'
                    }`}
                  >
                    {isActive && (
                      <motion.div
                        layoutId="nav-active"
                        className="absolute inset-0 rounded-2xl bg-[#F97316]"
                        transition={{ type: 'spring', damping: 24, stiffness: 280 }}
                      />
                    )}
                    <span className={`relative z-10 grid h-9 w-9 place-items-center rounded-xl ${isActive ? 'bg-white/15' : 'bg-white/5'}`}>
                      <item.icon size={18} />
                    </span>
                    <span className="relative z-10">{item.label}</span>
                  </motion.div>
                )}
              </NavLink>
            ))}
          </nav>

          <div className="mt-auto rounded-[24px] bg-white/8 border border-white/10 p-3 flex items-center gap-3">
            <div className="grid place-items-center h-11 w-11 rounded-2xl bg-white text-[#111827] text-sm font-bold">
              {initials}
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-sm font-semibold text-white truncate">{user?.full_name || 'Admin'}</div>
              <div className="text-xs text-slate-400 truncate">{user?.email}</div>
            </div>
            <button
              onClick={handleLogout}
              title="Log out"
              className="grid place-items-center h-9 w-9 rounded-xl bg-white/10 hover:bg-[#EF4444] hover:text-white text-slate-300 transition"
            >
              <LogOut size={16} />
            </button>
          </div>
        </aside>

        {/* Main */}
        <main className="flex-1 min-w-0">
          <header className="mb-5 hidden md:flex items-center justify-between gap-4">
            <div className="relative flex-1 max-w-2xl">
              <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                aria-label="Search"
                placeholder="Search projects, tasks, team..."
                className="h-[52px] w-full rounded-full border border-[#E5E7EB] bg-white py-3 pl-12 pr-5 text-sm text-[#111827] outline-none shadow-[0_12px_30px_rgba(17,24,39,0.04)] transition focus:border-[#F97316] focus:ring-4 focus:ring-orange-100"
              />
            </div>
            <div className="flex items-center gap-3">
              <button title="Notifications" className="grid h-12 w-12 place-items-center rounded-full border border-[#E5E7EB] bg-white text-slate-500 shadow-[0_12px_30px_rgba(17,24,39,0.04)] hover:text-[#F97316]">
                <Bell size={18} />
              </button>
              <div className="flex items-center gap-3 rounded-full border border-[#E5E7EB] bg-white py-1.5 pl-2 pr-4 shadow-[0_12px_30px_rgba(17,24,39,0.04)]">
                <div className="grid h-9 w-9 place-items-center rounded-full bg-[#111827] text-xs font-bold text-white">{initials}</div>
                <div className="leading-tight">
                  <div className="text-sm font-semibold text-[#111827]">{user?.full_name || 'Admin'}</div>
                  <div className="text-xs text-[#6B7280]">Workspace</div>
                </div>
              </div>
            </div>
          </header>
          {/* Mobile top nav */}
          <div className="md:hidden glass rounded-[24px] p-2 mb-4 flex items-center gap-1 overflow-x-auto">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `flex items-center gap-2 rounded-2xl px-3 py-2 text-sm whitespace-nowrap ${
                    isActive ? 'bg-[#F97316] text-white font-semibold' : 'text-slate-500'
                  }`
                }
              >
                <item.icon size={16} /> {item.label}
              </NavLink>
            ))}
          </div>

          <div className="pb-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
