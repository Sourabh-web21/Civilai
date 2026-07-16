import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import {
  ArrowRight, CalendarCheck, Check, ChevronRight, CircleDot,
  Clock3, ExternalLink, FileText, Inbox, Link2, Mail,
  Mic2, RefreshCw, Settings2, ShieldCheck, Sparkles,
} from 'lucide-react'
import { PageWrap } from '../components/ui'
import { api, errMessage, unwrap } from '../api/client'

const mailFlow = [
  { title: 'Mailbox sync starts', detail: 'IMAP safely checks the connected inbox', icon: Inbox },
  { title: 'Activity is tracked', detail: 'AiConnect lists newly detected email and attachment counts', icon: Mail },
  { title: 'Attachments are saved', detail: 'Supported files are handed to the separate RAG document pipeline', icon: FileText },
]

const meetingFlow = [
  { title: 'Find meeting links', detail: 'Detected from synced email or pasted manually', icon: Link2 },
  { title: 'Capture locally', detail: 'The recorder captures system audio and feeds transcription', icon: Mic2 },
  { title: 'Prepare MOM', detail: 'Transcript, decisions and actions are generated after capture', icon: FileText },
 ]

const recentMail = [
  { sender: 'Mailbox activity', subject: 'Sync to see recent email and attachments', time: 'Ready', tag: 'IMAP' },
]

function StatusPill({ children, active = false }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ${
      active ? 'bg-[#F0FDF4] text-[#15803D]' : 'bg-[#FFF7ED] text-[#C2410C]'
    }`}>
      <CircleDot size={12} /> {children}
    </span>
  )
}

function Flow({ items }) {
  return (
    <div className="grid gap-3 lg:grid-cols-3">
      {items.map((item, index) => (
        <div key={item.title} className="relative flex gap-3 rounded-2xl border border-[#E5E7EB] bg-[#F9FAFB] p-4">
          <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-white text-[#F97316]">
            <item.icon size={18} />
          </div>
          <div>
            <p className="text-sm font-semibold text-[#111827]">{item.title}</p>
            <p className="mt-1 text-xs leading-5 text-[#6B7280]">{item.detail}</p>
          </div>
          {index < items.length - 1 ? <ChevronRight className="absolute -right-4 top-7 z-10 hidden text-[#CBD5E1] lg:block" size={18} /> : null}
        </div>
      ))}
    </div>
  )
}

export default function AiConnect() {
  const [meetingLink, setMeetingLink] = useState('')
  const [scheduled, setScheduled] = useState(false)
  const [meetingStarting, setMeetingStarting] = useState(false)
  const [meetingSession, setMeetingSession] = useState(null)
  const [meetingStatus, setMeetingStatus] = useState('')
  const [meetingError, setMeetingError] = useState('')
  const [mom, setMom] = useState('')
  const [mailLoading, setMailLoading] = useState(false)
  const [mailError, setMailError] = useState('')
  const [syncedMail, setSyncedMail] = useState([])
  const [mailSummary, setMailSummary] = useState(null)
  const [detectedMeetings, setDetectedMeetings] = useState([])
  const [emailDraft, setEmailDraft] = useState({ action: 'compose', to: '', subject: '', prompt: '' })
  const [emailPreview, setEmailPreview] = useState(null)
  const [emailSending, setEmailSending] = useState(false)
  const [emailSendStatus, setEmailSendStatus] = useState('')
  const [localMeeting, setLocalMeeting] = useState(null)
  const [localTranscript, setLocalTranscript] = useState([])
  const [localMeetingTitle, setLocalMeetingTitle] = useState('')
  const [localMeetingLoading, setLocalMeetingLoading] = useState(false)
  const [localMeetingError, setLocalMeetingError] = useState('')
  const [localBackend, setLocalBackend] = useState(null)
  const [exportStatus, setExportStatus] = useState('')
  const [recordingSeconds, setRecordingSeconds] = useState(0)
  const [offlineModels, setOfflineModels] = useState([])
  const [modelJobs, setModelJobs] = useState({})
  const emailComposerRef = useRef(null)
  const emailPromptRef = useRef(null)

  const handleConnectEmail = async () => {
    setMailLoading(true)
    setMailError('')
    try {
      const response = await api.post('/api/v1/project/extract')
      const result = unwrap(response) || {}
      setSyncedMail(result.recent_emails || result.emails_extracted || [])
      setMailSummary(result)
      setDetectedMeetings(result.detected_meetings || [])
    } catch (error) {
      if (error?.response?.status !== 429) setMailError(errMessage(error))
    } finally {
      setMailLoading(false)
    }
  }

  useEffect(() => {
    // The short delay avoids duplicate initial calls from React StrictMode's
    // development-only mount/unmount cycle.
    const initialId = window.setTimeout(handleConnectEmail, 100)
    const intervalId = window.setInterval(handleConnectEmail, 15 * 1000)
    return () => {
      window.clearTimeout(initialId)
      window.clearInterval(intervalId)
    }
  }, [])

  const handlePrepareDraft = (event) => {
    event.preventDefault()
    setEmailSendStatus('')
    setEmailPreview({ ...emailDraft, body: emailDraft.prompt.trim() })
  }

  const handleSendEmail = async () => {
    if (!emailPreview) return
    setEmailSending(true)
    setEmailSendStatus('')
    try {
      await api.post('/api/v1/project/email/action', {
        action: emailPreview.action,
        to: emailPreview.to,
        subject: emailPreview.subject,
        body: emailPreview.body,
        original_message_id: emailPreview.original_message_id || '',
      })
      setEmailSendStatus('Email sent successfully.')
      setEmailPreview(null)
      setEmailDraft({ action: 'compose', to: '', subject: '', prompt: '' })
    } catch (error) {
      setEmailSendStatus(errMessage(error))
    } finally {
      setEmailSending(false)
    }
  }

  const handleUseMail = (mail, action) => {
    const sourceText = mail.description?.trim() || '(No plain-text body was available from this message.)'
    setEmailDraft({
      action,
      original_message_id: mail.message_id || '',
      to: action === 'reply' ? (mail.sender?.match(/<([^>]+)>/)?.[1] || mail.sender || '') : '',
      subject: mail.subject || '',
      prompt: action === 'forward'
        ? `Forwarding this email for your review:\n\n${sourceText}`
        : action === 'reply'
          ? `Write a clear reply to this email:\n\n${sourceText}`
          : '',
    })
    setEmailPreview(null)
    setEmailSendStatus('')
    window.requestAnimationFrame(() => {
      emailComposerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      emailPromptRef.current?.focus()
    })
  }

  const handleSchedule = async (event) => {
    event.preventDefault()
    if (!meetingLink.trim()) return
    setMeetingStarting(true)
    setMeetingError('')
    setMom('')
    try {
      setLocalMeetingTitle((current) => current || `Meeting capture · ${meetingLink.trim()}`)
      const response = await api.post('/api/v1/project/local-meeting/start', {
        title: `Meeting capture · ${meetingLink.trim()}`,
        audio_source: 'system',
      })
      const meeting = unwrap(response)
      setLocalMeeting(meeting)
      setLocalTranscript([])
      setRecordingSeconds(0)
      setMeetingStatus('Recording locally. The meeting link is saved as session context.')
      setScheduled(true)
    } catch (error) {
      setMeetingError(errMessage(error))
    } finally {
      setMeetingStarting(false)
    }
  }

  useEffect(() => {
    const loadBackend = async () => {
      try {
        const response = await api.get('/api/v1/project/local-meeting/backend-status')
        setLocalBackend(unwrap(response)?.audio || null)
      } catch {
        setLocalBackend(null)
      }
    }
    loadBackend()
  }, [])

  const loadOfflineModels = async () => {
    try {
      const response = await api.get('/api/v1/project/offline-models')
      setOfflineModels(unwrap(response) || [])
    } catch {
      setOfflineModels([])
    }
  }

  useEffect(() => {
    loadOfflineModels()
  }, [])

  useEffect(() => {
    const activeJobs = Object.values(modelJobs).filter((job) => ['queued', 'downloading', 'verifying'].includes(job?.status))
    if (!activeJobs.length) return undefined
    const poll = async () => {
      const updates = {}
      await Promise.all(activeJobs.map(async (job) => {
        try {
          const response = await api.get(`/api/v1/project/offline-models/${job.model_id}/download`)
          const result = unwrap(response) || {}
          if (result.job) updates[job.model_id] = result.job
        } catch {
          updates[job.model_id] = { ...job, status: 'failed', error: 'Unable to read download status.' }
        }
      }))
      if (Object.keys(updates).length) setModelJobs((current) => ({ ...current, ...updates }))
      loadOfflineModels()
    }
    const intervalId = window.setInterval(poll, 1500)
    return () => window.clearInterval(intervalId)
  }, [modelJobs])

  useEffect(() => {
    if (!localMeeting || localMeeting.status === 'completed') return undefined

    const pollLocalMeeting = async () => {
      try {
        const [statusResponse, detailResponse] = await Promise.all([
          api.get(`/api/v1/project/local-meeting/${localMeeting.id}/status`),
          api.get(`/api/v1/project/local-meeting/${localMeeting.id}`),
        ])
        const statusResult = unwrap(statusResponse) || {}
        const detailResult = unwrap(detailResponse) || {}
        setLocalMeeting((current) => ({ ...(current || {}), ...detailResult, status: statusResult.status || detailResult.status }))
        setLocalTranscript(detailResult.segments || [])
        setMeetingStatus(statusResult.message || detailResult.status || 'Recording...')
        if (statusResult.error_message) setLocalMeetingError(statusResult.error_message)
      } catch (error) {
        setLocalMeetingError(errMessage(error))
      }
    }

    const initialId = window.setTimeout(pollLocalMeeting, 1000)
    const intervalId = window.setInterval(pollLocalMeeting, 3000)
    return () => {
      window.clearTimeout(initialId)
      window.clearInterval(intervalId)
    }
  }, [localMeeting?.id, localMeeting?.status])

  useEffect(() => {
    if (!localMeeting || ['completed', 'failed', 'cancelled'].includes(localMeeting.status)) return undefined
    const startedAt = localMeeting.started_at ? new Date(localMeeting.started_at).getTime() : Date.now()
    const tick = () => setRecordingSeconds(Math.max(0, Math.floor((Date.now() - startedAt) / 1000)))
    tick()
    const intervalId = window.setInterval(tick, 1000)
    return () => window.clearInterval(intervalId)
  }, [localMeeting?.id, localMeeting?.status, localMeeting?.started_at])

  const startLocalMeeting = async () => {
    setLocalMeetingLoading(true)
    setLocalMeetingError('')
    setMom('')
    setExportStatus('')
    setLocalTranscript([])
    try {
      const response = await api.post('/api/v1/project/local-meeting/start', {
        title: meetingLink ? `${localMeetingTitle || 'Local meeting'} · ${meetingLink}` : (localMeetingTitle || 'Local meeting'),
        audio_source: 'system',
      })
      const meeting = unwrap(response)
      setLocalMeeting(meeting)
      setRecordingSeconds(0)
      setMeetingStatus('Recording...')
    } catch (error) {
      setLocalMeetingError(errMessage(error))
    } finally {
      setLocalMeetingLoading(false)
    }
  }

  const stopLocalMeeting = async () => {
    if (!localMeeting) return
    setLocalMeetingLoading(true)
    setLocalMeetingError('')
    try {
      const response = await api.post(`/api/v1/project/local-meeting/${localMeeting.id}/stop`)
      const result = unwrap(response) || {}
      setLocalMeeting(result.meeting)
      setMom(result.mom || '')
      setMeetingStatus('Completed')
    } catch (error) {
      setLocalMeetingError(errMessage(error))
    } finally {
      setLocalMeetingLoading(false)
    }
  }

  const exportLocalMeeting = async (format) => {
    if (!localMeeting) return
    setExportStatus('')
    try {
      const response = await api.post(`/api/v1/project/local-meeting/${localMeeting.id}/export`, { export_format: format })
      const result = unwrap(response) || {}
      setExportStatus(`${format.toUpperCase()} export created: ${result.file_path}`)
    } catch (error) {
      setExportStatus(errMessage(error))
    }
  }

  const startModelDownload = async (model) => {
    try {
      const response = await api.post(`/api/v1/project/offline-models/${model.id}/download`)
      const result = unwrap(response) || {}
      if (result.job) setModelJobs((current) => ({ ...current, [model.id]: result.job }))
      loadOfflineModels()
    } catch (error) {
      setModelJobs((current) => ({
        ...current,
        [model.id]: { model_id: model.id, status: 'failed', error: errMessage(error) },
      }))
    }
  }

  const formatDuration = (seconds) => {
    const safeSeconds = Math.max(0, Number(seconds) || 0)
    const hours = Math.floor(safeSeconds / 3600)
    const minutes = Math.floor((safeSeconds % 3600) / 60)
    const secs = safeSeconds % 60
    return [hours, minutes, secs].map((value) => String(value).padStart(2, '0')).join(':')
  }

  const formatModelProgress = (job) => {
    if (!job) return ''
    if (job.status === 'failed') return job.error || 'Download failed'
    if (job.status === 'complete') return 'Downloaded'
    if (!job.total_bytes) return job.status
    return `${Math.round((job.downloaded_bytes / job.total_bytes) * 100)}%`
  }

  return (
    <PageWrap>
      <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-[#F97316]">
            <PlugMark /> AI workspace integrations
          </div>
          <h1 className="font-display text-3xl font-bold text-[#111827]">AiConnect</h1>
          <p className="mt-1 max-w-2xl text-[#6B7280]">Turn email and meetings into searchable project knowledge, replies and action items.</p>
        </div>
        
      </div>

      <div className="mb-6 grid gap-3 sm:grid-cols-3">
          <Metric icon={Mail} label="Email connection" value={mailSummary ? 'Connected' : 'Ready to test'} note={mailSummary ? `${mailSummary.email_account || 'Mailbox'} · ${mailSummary.messages_checked} checked` : 'IMAP extractor available'} />
        <Metric icon={Mic2} label="Meeting assistant" value={localBackend?.ready ? 'Ready locally' : 'Audio setup needed'} note={localBackend?.backend || 'Checking recorder'} />
        <Metric icon={Settings2} label="Offline models" value={`${offlineModels.filter((model) => model.downloaded).length}/${offlineModels.length || 0} ready`} note="Speech and local LLM" />
      </div>

      <section className="glass overflow-hidden rounded-[28px]">
        <div className="border-b border-[#E5E7EB] p-5 sm:p-7">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex gap-4">
              <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-[#FFF7ED] text-[#F97316]"><Mail size={22} /></div>
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="font-display text-xl font-bold text-[#111827]">Email Intelligence</h2>
                  <StatusPill active={Boolean(mailSummary)}>{mailSummary ? `Connected: ${mailSummary.email_account || 'mailbox'}` : 'Needs credentials'}</StatusPill>
                </div>
                <p className="mt-1 max-w-2xl text-sm leading-6 text-[#6B7280]">Synchronize and track incoming mailbox activity, then compose, reply or forward through the reviewed Email Actions workflow below.</p>
              </div>
            </div>
            <StatusPill active><RefreshCw className={mailLoading ? 'animate-spin' : ''} size={12} /> {mailLoading ? 'Synchronizing…' : 'Auto-sync every 15 seconds'}</StatusPill>
          </div>
          {mailError ? <p role="alert" className="mt-4 rounded-2xl bg-[#FEF2F2] px-4 py-3 text-sm text-[#B91C1C]">{mailError}</p> : null}
          {mailSummary ? <p role="status" className="mt-4 rounded-2xl bg-[#F0FDF4] px-4 py-3 text-sm text-[#15803D]">Mailbox checked safely: {mailSummary.messages_checked} messages scanned, {mailSummary.emails_extracted?.length || 0} new messages processed, and the latest {syncedMail.length} shown below. {mailSummary.rag_reload_queued ? 'New attachments will be available to RAG on the next question.' : 'No new attachments were found.'}</p> : null}
          <div className="mt-6"><Flow items={mailFlow} /></div>
        </div>

        <div className="grid lg:grid-cols-[1.2fr_.8fr]">
          <div className="border-b border-[#E5E7EB] p-5 sm:p-7 lg:border-b-0 lg:border-r">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <h3 className="font-semibold text-[#111827]">Live mail activity</h3>
                <p className="mt-1 text-xs text-[#6B7280]">{mailSummary ? 'Latest mailbox sync' : 'Preview data · connect IMAP for live updates'}</p>
              </div>
              <span className="text-xs font-medium text-[#22C55E]">Automatic</span>
            </div>
            <div className="divide-y divide-[#E5E7EB] rounded-2xl border border-[#E5E7EB]">
              {(mailSummary ? syncedMail.map((mail, index) => ({
                ...mail,
                sender: mail.sender || 'Incoming email',
                subject: mail.subject || 'No subject',
                time: mail.date || (index === 0 ? 'Just synced' : 'New'),
                tag: mail.attachments?.length ? `${mail.attachments.length} attachment(s) indexed` : 'No attachment',
              })) : recentMail).map((mail) => (
                <div key={`${mail.subject}-${mail.time}`} className="flex items-start gap-3 p-4">
                  <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-[#F97316]" />
                  <div className="min-w-0 flex-1">
                    <div className="flex justify-between gap-3"><p className="truncate text-sm font-semibold text-[#111827]">{mail.sender}</p><span className="shrink-0 text-xs text-[#9CA3AF]">{mail.time}</span></div>
                    <p className="mt-0.5 truncate text-sm text-[#6B7280]">{mail.subject}</p>
                    <span className="mt-2 inline-block rounded-full bg-[#F9FAFB] px-2.5 py-1 text-[11px] font-medium text-[#6B7280]">{mail.tag}</span>
                    {mailSummary ? <span className="ml-2 inline-flex gap-2"><button type="button" onClick={() => handleUseMail(mail, 'reply')} className="text-[11px] font-semibold text-[#F97316]">Reply</button><button type="button" onClick={() => handleUseMail(mail, 'forward')} className="text-[11px] font-semibold text-[#F97316]">Forward</button></span> : null}
                  </div>
                </div>
              ))}
              {mailSummary && syncedMail.length === 0 ? <div className="p-5 text-center text-sm text-[#6B7280]">No new mail was found in this sync window.</div> : null}
            </div>
          </div>
          <div className="border-t border-[#E5E7EB] p-5 sm:p-7 lg:border-t-0">
            <div className="flex items-center gap-2"><Link2 size={18} className="text-[#F97316]" /><h3 className="font-semibold text-[#111827]">Meeting links</h3></div>
            <p className="mt-2 text-sm leading-6 text-[#6B7280]">Detected links from mailbox sync appear here. You can also paste a Google Meet, Teams or Zoom link below.</p>
            <div className="mt-4 space-y-2">
              {detectedMeetings.slice().reverse().slice(0, 3).map((meeting) => (
                <button key={meeting.url} type="button" disabled={meeting.expired} onClick={() => { setMeetingLink(meeting.url); setScheduled(false); setMeetingError('') }} className={`block w-full rounded-2xl border border-[#E5E7EB] bg-white p-3 text-left transition ${meeting.expired ? 'cursor-not-allowed opacity-60' : 'hover:border-[#F97316]'}`}>
                  <span className="block truncate text-sm font-semibold text-[#111827]">{meeting.subject || 'Meeting invitation'} {meeting.expired ? '(Expired)' : ''}</span>
                  <span className="mt-1 block truncate text-xs text-[#6B7280]">{meeting.url}</span>
                </button>
              ))}
              {!detectedMeetings.length ? <p className="rounded-2xl border border-dashed border-[#CBD5E1] p-4 text-xs text-[#6B7280]">No meeting link detected yet.</p> : null}
            </div>
          </div>
        </div>
      </section>

      <section className="glass mt-6 overflow-hidden rounded-[28px]">
        <div className="border-b border-[#E5E7EB] p-5 sm:p-7">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex gap-4">
              <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-[#FFF7ED] text-[#F97316]"><Settings2 size={22} /></div>
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="font-display text-xl font-bold text-[#111827]">Offline Models</h2>
                  <StatusPill active={offlineModels.some((model) => model.downloaded)}>Local cache</StatusPill>
                </div>
                <p className="mt-1 max-w-2xl text-sm leading-6 text-[#6B7280]">Download speech and language models once, verify them locally, and use them without cloud APIs after setup.</p>
              </div>
            </div>
          </div>
        </div>
        <div className="grid gap-3 p-5 sm:p-7 lg:grid-cols-2">
          {offlineModels.map((model) => {
            const job = modelJobs[model.id]
            const running = ['queued', 'downloading', 'verifying'].includes(job?.status)
            const progress = formatModelProgress(job)
            return (
              <div key={model.id} className="rounded-2xl border border-[#E5E7EB] bg-[#F9FAFB] p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-[#111827]">{model.label}</p>
                    <p className="mt-1 text-xs text-[#6B7280]">{model.kind.toUpperCase()} · {model.size_mb} MB · {model.min_ram_gb} GB RAM</p>
                  </div>
                  <StatusPill active={model.downloaded}>{model.downloaded ? 'Ready' : model.download_configured ? 'Available' : 'Unavailable'}</StatusPill>
                </div>
                <p className="mt-3 text-xs leading-5 text-[#6B7280]">
                  {model.downloaded ? 'Installed and ready for local processing.' : model.sha256_verified ? 'Download will be verified before use.' : model.checksum ? `${model.checksum_algorithm.toUpperCase()} integrity check available.` : 'Checksum not published by the model host; download is still supported.'}
                </p>
                {job ? (
                  <div className="mt-3">
                    <div className="h-2 overflow-hidden rounded-full bg-white">
                      <div className="h-full bg-[#F97316]" style={{ width: job.total_bytes ? `${Math.min(100, Math.round((job.downloaded_bytes / job.total_bytes) * 100))}%` : running ? '20%' : job.status === 'complete' ? '100%' : '0%' }} />
                    </div>
                    <p className={`mt-2 text-xs font-medium ${job.status === 'failed' ? 'text-[#B91C1C]' : 'text-[#6B7280]'}`}>{progress}</p>
                  </div>
                ) : null}
                <button type="button" onClick={() => startModelDownload(model)} disabled={model.downloaded || running || !model.download_configured} className="btn btn-ghost mt-4 text-xs">
                  {running ? <RefreshCw className="animate-spin" size={14} /> : <ExternalLink size={14} />} {model.downloaded ? 'Downloaded' : 'Download'}
                </button>
              </div>
            )
          })}
          {offlineModels.length === 0 ? <div className="rounded-2xl border border-dashed border-[#CBD5E1] p-8 text-center text-sm text-[#6B7280]">Offline model registry is not available.</div> : null}
        </div>
      </section>

      <section className="glass mt-6 overflow-hidden rounded-[28px]">
        <div className="border-b border-[#E5E7EB] p-5 sm:p-7">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex gap-4">
              <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-[#FFF7ED] text-[#F97316]"><Mic2 size={22} /></div>
              <div>
                <div className="flex flex-wrap items-center gap-2"><h2 className="font-display text-xl font-bold text-[#111827]">Meeting Assistant · Local Recorder + MOM</h2><StatusPill active={localMeeting?.status === 'completed'}>{meetingStatus || 'Ready'}</StatusPill></div>
                <p className="mt-1 max-w-2xl text-sm leading-6 text-[#6B7280]">Capture local meeting audio, stream transcript segments, build chunk summaries, and export Minutes of Meeting from this device.</p>
              </div>
            </div>
            <StatusPill active={Boolean(localBackend)}>{localBackend?.backend || 'Checking backend'}</StatusPill>
          </div>
          {localBackend && !localBackend.ready ? <p className="mt-4 rounded-2xl bg-[#FFF7ED] px-4 py-3 text-sm text-[#C2410C]">{localBackend.message}</p> : null}
          {localMeetingError ? <p role="alert" className="mt-4 rounded-2xl bg-[#FEF2F2] px-4 py-3 text-sm text-[#B91C1C]">{localMeetingError}</p> : null}
        </div>

        <div className="grid border-b border-[#E5E7EB] lg:grid-cols-[.85fr_1.15fr]">
          <div className="border-b border-[#E5E7EB] p-5 sm:p-7 lg:border-b-0 lg:border-r">
            <label className="label" htmlFor="local-meeting-title">Meeting title</label>
            <input id="local-meeting-title" className="field" value={localMeetingTitle} onChange={(event) => setLocalMeetingTitle(event.target.value)} placeholder="Weekly progress review" />
            <label className="label mt-4" htmlFor="local-meeting-link">Optional Google Meet, Zoom or Teams link</label>
            <input id="local-meeting-link" type="url" className="field" value={meetingLink} onChange={(event) => setMeetingLink(event.target.value)} placeholder="https://meet.google.com/abc-defg-hij" />
            <div className="mt-4 flex flex-wrap gap-3">
              <button type="button" onClick={startLocalMeeting} disabled={localMeetingLoading || (localMeeting && localMeeting.status !== 'completed')} className="btn btn-primary">{localMeetingLoading ? <RefreshCw className="animate-spin" size={16} /> : <Mic2 size={16} />} Start Meeting</button>
              <button type="button" onClick={stopLocalMeeting} disabled={!localMeeting || localMeeting.status === 'completed' || localMeetingLoading} className="btn btn-ghost"><Check size={16} /> Stop & build MOM</button>
            </div>
            {localMeeting ? (
              <div className="mt-5 rounded-2xl border border-[#E5E7EB] bg-[#F9FAFB] p-4 text-sm text-[#4B5563]">
                <p className="font-semibold text-[#111827]">Session #{localMeeting.id}</p>
                <p className="mt-1">Status: {localMeeting.status}</p>
                <p className="mt-1">Timer: {formatDuration(localMeeting.duration_seconds || recordingSeconds)}</p>
                <p className="mt-1">Segments: {localTranscript.length || localMeeting.segment_count || 0}</p>
              </div>
            ) : null}
            <p className="mt-3 text-xs leading-5 text-[#6B7280]">The link is saved as meeting context. CivilAI records this device locally and does not require Vexa.</p>
          </div>
          <div className="p-5 sm:p-7">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2"><Clock3 size={18} className="text-[#F97316]" /><h3 className="font-semibold text-[#111827]">Live transcript</h3></div>
              <span className="text-xs font-semibold text-[#6B7280]">{localTranscript.length} segments</span>
            </div>
            <div className="mt-4 min-h-[220px] max-h-[360px] overflow-y-auto rounded-2xl border border-[#E5E7EB] bg-white p-4">
              {localTranscript.length ? localTranscript.map((segment) => (
                <div key={segment.id || segment.sequence} className="border-b border-[#F3F4F6] py-3 last:border-0">
                  <p className="text-[11px] font-semibold text-[#F97316]">{Math.round(segment.start_seconds)}s - {Math.round(segment.end_seconds)}s</p>
                  <p className="mt-1 text-sm leading-6 text-[#374151]">{segment.text}</p>
                </div>
              )) : <div className="grid h-[180px] place-items-center text-center text-sm text-[#6B7280]">Transcript segments will appear here while the meeting runs.</div>}
            </div>
          </div>
        </div>

        {mom ? <div className="p-5 sm:p-7"><div className="flex flex-wrap items-center justify-between gap-3"><div className="flex items-center gap-2"><FileText className="text-[#F97316]" size={19} /><h3 className="font-semibold text-[#111827]">Minutes of Meeting</h3></div><div className="flex flex-wrap gap-2">{['markdown', 'txt', 'docx', 'pdf'].map((format) => <button key={format} type="button" onClick={() => exportLocalMeeting(format)} className="btn btn-ghost text-xs">{format.toUpperCase()}</button>)}</div></div><div className="mt-4 whitespace-pre-wrap rounded-2xl border border-[#E5E7EB] bg-[#F9FAFB] p-5 text-sm leading-7 text-[#374151]">{mom}</div>{exportStatus ? <p role="status" className="mt-3 text-sm font-medium text-[#15803D]">{exportStatus}</p> : null}</div> : null}
      </section>

      <section className="glass mt-6 overflow-hidden rounded-[28px]">
        <div className="border-b border-[#E5E7EB] p-5 sm:p-7">
          <div className="flex items-start gap-4">
            <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-[#FFF7ED] text-[#F97316]"><Mail size={22} /></div>
            <div><h2 className="font-display text-xl font-bold text-[#111827]">Email Actions</h2><p className="mt-1 text-sm leading-6 text-[#6B7280]">Compose, reply or forward from your instruction. Every message is reviewed before SMTP sends it.</p></div>
          </div>
        </div>
        <div className="grid lg:grid-cols-2">
          <form ref={emailComposerRef} onSubmit={handlePrepareDraft} className="border-b border-[#E5E7EB] p-5 sm:p-7 lg:border-b-0 lg:border-r">
            <label className="label" htmlFor="email-action">Action</label>
            <select id="email-action" className="field" value={emailDraft.action} onChange={(event) => setEmailDraft({ ...emailDraft, action: event.target.value })}><option value="compose">Compose</option><option value="reply">Reply</option><option value="forward">Forward</option></select>
            <label className="label mt-4" htmlFor="email-to">To</label>
            <input id="email-to" type="text" required className="field" placeholder="person@example.com" value={emailDraft.to} onChange={(event) => setEmailDraft({ ...emailDraft, to: event.target.value })} />
            <label className="label mt-4" htmlFor="email-subject">Subject</label>
            <input id="email-subject" required maxLength={200} className="field" value={emailDraft.subject} onChange={(event) => setEmailDraft({ ...emailDraft, subject: event.target.value })} />
            <label className="label mt-4" htmlFor="email-prompt">Your instruction or message</label>
            <textarea ref={emailPromptRef} id="email-prompt" required rows={5} maxLength={10000} className="field resize-y" placeholder="Write the email you want to send…" value={emailDraft.prompt} onChange={(event) => setEmailDraft({ ...emailDraft, prompt: event.target.value })} />
            <button className="btn btn-primary mt-4" type="submit"><FileText size={16} /> Prepare draft</button>
          </form>
          <div className="p-5 sm:p-7">
            <h3 className="font-semibold text-[#111827]">Review before sending</h3>
            {emailPreview ? <div className="mt-4 rounded-2xl border border-[#E5E7EB] bg-[#F9FAFB] p-4"><p className="text-xs text-[#6B7280]">{emailPreview.action.toUpperCase()} · To: {emailPreview.to}</p><p className="mt-3 font-semibold text-[#111827]">{emailPreview.subject}</p><p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-[#4B5563]">{emailPreview.body}</p><div className="mt-5 flex gap-3"><button type="button" onClick={() => setEmailPreview(null)} className="btn btn-ghost">Edit</button><button type="button" onClick={handleSendEmail} disabled={emailSending} className="btn btn-primary">{emailSending ? <RefreshCw className="animate-spin" size={16} /> : <Mail size={16} />}{emailSending ? 'Sending…' : 'Confirm & send'}</button></div></div> : <div className="mt-4 rounded-2xl border border-dashed border-[#CBD5E1] p-8 text-center text-sm text-[#6B7280]">Complete the form to create a reviewable draft.</div>}
            {emailSendStatus ? <p role="status" className="mt-4 text-sm font-medium text-[#15803D]">{emailSendStatus}</p> : null}
          </div>
        </div>
      </section>

      {false && <section className="glass mt-6 overflow-hidden rounded-[28px]">
        <div className="p-5 sm:p-7">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex gap-4">
              <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-[#FFF7ED] text-[#F97316]"><CalendarCheck size={22} /></div>
              <div>
                <div className="flex flex-wrap items-center gap-2"><h2 className="font-display text-xl font-bold text-[#111827]">Meeting Assistant</h2><StatusPill>Not connected</StatusPill></div>
                <p className="mt-1 max-w-2xl text-sm leading-6 text-[#6B7280]">Detect meeting invitations from email or paste a link manually. CivilAI can produce minutes of meeting (MOM) after a meeting-bot provider is connected.</p>
              </div>
            </div>
          </div>
         
        </div>

        <div className="grid border-t border-[#E5E7EB] lg:grid-cols-2">
          <div className="border-b border-[#E5E7EB] p-5 sm:p-7 lg:border-b-0 lg:border-r">
            <div className="flex items-center gap-2"><Inbox size={18} className="text-[#F97316]" /><h3 className="font-semibold text-[#111827]">Automatic from email</h3></div>
            <p className="mt-2 text-sm leading-6 text-[#6B7280]">When mailbox monitoring is enabled, CivilAI can detect Google Meet, Microsoft Teams and Zoom links and ask before joining.</p>
            <div className="mt-4 flex items-center gap-3 rounded-2xl border border-dashed border-[#FDBA74] bg-[#FFF7ED] p-4">
              <Clock3 size={20} className="shrink-0 text-[#F97316]" />
              <div><p className="text-sm font-semibold text-[#111827]">Waiting for email connection</p><p className="mt-0.5 text-xs text-[#6B7280]">Invite detection starts after mailbox setup.</p></div>
            </div>
            {detectedMeetings.length ? <div className="mt-4 space-y-2">{detectedMeetings.slice().reverse().slice(0, 5).map((meeting) => <button key={meeting.url} type="button" onClick={() => { setMeetingLink(meeting.url); setScheduled(false); setMeetingError('') }} className="block w-full rounded-2xl border border-[#E5E7EB] bg-white p-3 text-left transition hover:border-[#F97316]"><span className="block truncate text-sm font-semibold text-[#111827]">{meeting.subject || 'Meeting invitation'}</span><span className="mt-1 block truncate text-xs text-[#6B7280]">{meeting.url}</span></button>)}</div> : null}
          </div>
          <form onSubmit={handleSchedule} className="p-5 sm:p-7">
            <div className="flex items-center gap-2"><Link2 size={18} className="text-[#F97316]" /><h3 className="font-semibold text-[#111827]">Paste a meeting link</h3></div>
            <label className="label mt-4" htmlFor="meeting-link">Google Meet, Teams or Zoom URL</label>
            <input id="meeting-link" type="url" required className="field" value={meetingLink} onChange={(event) => { setMeetingLink(event.target.value); setScheduled(false); setMeetingSession(null); setMom(''); setMeetingError('') }} placeholder="https://meet.google.com/abc-defg-hij" />
            <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
              <span className="text-xs text-[#6B7280]">MOM appears here automatically after the meeting ends.</span>
              <button className="btn btn-primary" disabled={meetingStarting} type="submit">{meetingStarting ? <RefreshCw className="animate-spin" size={16} /> : <ArrowRight size={16} />}{meetingStarting ? 'Starting bot…' : 'Start assistant'}</button>
            </div>
            {scheduled ? <p role="status" className="mt-3 flex items-start gap-2 text-sm font-medium text-[#15803D]"><Check className="mt-0.5 shrink-0" size={16} /> {meetingStatus}</p> : null}
            {meetingError ? <p role="alert" className="mt-3 text-sm font-medium text-[#B91C1C]">{meetingError}</p> : null}
          </form>
        </div>
        {mom ? <div className="border-t border-[#E5E7EB] p-5 sm:p-7"><div className="flex items-center gap-2"><FileText className="text-[#F97316]" size={19} /><h3 className="font-semibold text-[#111827]">Minutes of Meeting</h3></div><div className="mt-4 whitespace-pre-wrap rounded-2xl border border-[#E5E7EB] bg-[#F9FAFB] p-5 text-sm leading-7 text-[#374151]">{mom}</div></div> : null}
      </section>}

    </PageWrap>
  )
}

function PlugMark() {
  return <span className="grid h-6 w-6 place-items-center rounded-lg bg-[#FFF7ED]"><Sparkles size={13} /></span>
}

function Metric({ icon: Icon, label, value, note }) {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass flex items-center gap-3 rounded-[22px] p-4">
      <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#FFF7ED] text-[#F97316]"><Icon size={18} /></div>
      <div className="min-w-0"><p className="text-xs text-[#6B7280]">{label}</p><p className="truncate text-sm font-bold text-[#111827]">{value}</p><p className="truncate text-[11px] text-[#9CA3AF]">{note}</p></div>
    </motion.div>
  )
}

function Permission({ icon: Icon, children }) {
  return <div className="flex items-start gap-2"><Icon size={16} className="mt-0.5 shrink-0 text-[#F97316]" /><span className="text-xs leading-5">{children}</span></div>
}
