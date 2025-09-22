import React, { useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import {
  LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip,
  ResponsiveContainer, BarChart, Bar, Legend
} from 'recharts'

type Repo = { id: number; owner: string; name: string; full_name: string; default_branch: string | null }
type Overview = { total: number; successRate: number; failureRate: number; avgDurationSecs: number; lastBuild: any }
type Run = {
  id:number; repo:string; workflow_name:string; head_branch:string;
  status:string; conclusion:string; duration_secs:number; url:string; started_at:string
}
type Job = {
  id:number; name:string; status:string; conclusion:string; started_at:string; completed_at:string; duration_secs:number
}

const fmtDuration = (secs:number) => {
  if (!secs && secs !== 0) return '-'
  const m = Math.floor(secs/60)
  const s = Math.floor(secs%60)
  return `${m}m ${s}s`
}

const StatusBadge: React.FC<{conclusion?:string}> = ({ conclusion }) => {
  const cls =
    conclusion === 'success' ? 'badge badge-success' :
    conclusion === 'failure' ? 'badge badge-failure' : 'badge badge-other'
  return <span className={cls}>{conclusion ?? 'other'}</span>
}

const Toggle: React.FC<{checked:boolean; onChange:(v:boolean)=>void; label:string}> = ({checked,onChange,label}) => (
  <button
    className={`btn ${checked ? 'btn-primary' : ''}`}
    onClick={() => onChange(!checked)}
    type="button"
    aria-pressed={checked}
  >
    {label} {checked ? 'On' : 'Off'}
  </button>
)

const DarkModeSwitch: React.FC = () => {
  const [dark, setDark] = useState<boolean>(() => document.documentElement.classList.contains('dark'))
  useEffect(() => {
    const root = document.documentElement
    dark ? root.classList.add('dark') : root.classList.remove('dark')
  }, [dark])
  return <Toggle checked={dark} onChange={setDark} label="Dark mode" />
}

const Loader: React.FC = () => (
  <div className="animate-pulse grid md:grid-cols-4 gap-4">
    {[...Array(4)].map((_,i)=>(
      <div key={i} className="kpi h-24" />
    ))}
  </div>
)

const Modal: React.FC<{open:boolean; onClose:()=>void; title:string; children:React.ReactNode}> = ({open,onClose,title,children}) => {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="card max-w-3xl w-full mx-4">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="text-lg font-semibold">{title}</h3>
          <button className="btn" onClick={onClose}>Close</button>
        </div>
        <div className="p-4">
          {children}
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [repos, setRepos] = useState<Repo[]>([])
  const [repo, setRepo] = useState<string>('')           // selected repo full name
  const [branch, setBranch] = useState<string>('')       // filter branch
  const [windowDays, setWindowDays] = useState<number>(7)
  const [overview, setOverview] = useState<Overview | null>(null)
  const [series, setSeries] = useState<any[]>([])
  const [runs, setRuns] = useState<Run[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // auto refresh
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [intervalSec, setIntervalSec] = useState(30)

  // run details modal
  const [openDetails, setOpenDetails] = useState(false)
  const [selectedRun, setSelectedRun] = useState<Run | null>(null)
  const [jobs, setJobs] = useState<Job[]>([])
  const [jobLog, setJobLog] = useState<string>('')

  const primaryRepo = useMemo(() => repo || (repos[0]?.full_name ?? ''), [repo, repos])

  const loadRepos = async () => {
    const r = await axios.get('/api/repos')
    setRepos(r.data)
    if (!repo && r.data[0]) setRepo(r.data[0].full_name)
  }

  const loadData = async () => {
    if (!primaryRepo) return
    setError(null)
    try {
      const [o, t, rs] = await Promise.all([
        axios.get('/api/metrics/overview', { params: { repo: primaryRepo, branch, windowDays }}),
        axios.get('/api/metrics/timeseries', { params: { repo: primaryRepo, branch, windowDays }}),
        axios.get('/api/runs', { params: { repo: primaryRepo, branch, limit: 50 }})
      ])
      setOverview(o.data)
      setSeries(t.data)
      setRuns(rs.data)
    } catch (e:any) {
      setError(e?.message || 'Failed to load')
    } finally {
      setLoading(false)
    }
  }

  const openRun = async (r: Run) => {
    setSelectedRun(r)
    setOpenDetails(true)
    setJobs([])
    setJobLog('')
    try {
      const j = await axios.get(`/api/runs/${r.id}/jobs`)
      setJobs(j.data)
      // quick peek: fetch first failed job log (if any)
      const failed = (j.data as Job[]).find(j => j.conclusion === 'failure')
      if (failed) {
        const log = await axios.get(`/api/jobs/${failed.id}/log`, { responseType: 'text' })
        setJobLog(log.data)
      }
    } catch { /* ignore */ }
  }

  useEffect(() => { loadRepos() }, [])
  useEffect(() => { if (primaryRepo) loadData() }, [primaryRepo, branch, windowDays])
  useEffect(() => {
    if (!autoRefresh) return
    const t = setInterval(() => loadData(), Math.max(5, intervalSec) * 1000)
    return () => clearInterval(t)
  }, [autoRefresh, intervalSec, primaryRepo, branch, windowDays])

  const successColor = "#10b981"   // emerald-500
  const failureColor = "#ef4444"   // red-500
  const otherColor   = "#f59e0b"   // amber-500
  const lineColor    = "#6366f1"   // indigo-500

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="px-6 py-4 border-b bg-white/70 backdrop-blur dark:bg-slate-900/60 sticky top-0 z-10">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">🚦 CI/CD Health Dashboard</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">Live metrics from GitHub Actions</p>
          </div>
          <div className="flex items-center gap-2">
            <DarkModeSwitch />
            <Toggle checked={autoRefresh} onChange={setAutoRefresh} label="Auto refresh" />
            <select
              className="px-3 py-2 rounded-lg border bg-white dark:bg-slate-900"
              value={intervalSec} onChange={e=>setIntervalSec(parseInt(e.target.value))}
            >
              <option value={15}>15s</option>
              <option value={30}>30s</option>
              <option value={60}>60s</option>
              <option value={120}>120s</option>
            </select>
          </div>
        </div>
      </header>

      <main className="p-6 space-y-6">
        {/* Filters */}
        <div className="card p-4 flex flex-wrap gap-3 items-center">
          <select className="px-3 py-2 rounded-lg border bg-white dark:bg-slate-900"
                  value={primaryRepo} onChange={e=>setRepo(e.target.value)}>
            {repos.map(r => <option key={r.id} value={r.full_name}>{r.full_name}</option>)}
          </select>
          <input className="px-3 py-2 rounded-lg border bg-white dark:bg-slate-900"
                 placeholder="branch (empty = all)" value={branch}
                 onChange={e=>setBranch(e.target.value)} />
          <select className="px-3 py-2 rounded-lg border bg-white dark:bg-slate-900"
                  value={windowDays} onChange={e=>setWindowDays(parseInt(e.target.value))}>
            <option value={3}>Last 3 days</option>
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
          </select>
        </div>

        {/* KPIs */}
        {loading ? <Loader /> : (
          <div className="grid md:grid-cols-4 gap-4">
            <div className="kpi">
              <div className="text-slate-500 text-sm">Success Rate</div>
              <div className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">{overview?.successRate ?? 0}%</div>
            </div>
            <div className="kpi">
              <div className="text-slate-500 text-sm">Failure Rate</div>
              <div className="text-3xl font-bold text-red-600 dark:text-red-400">{overview?.failureRate ?? 0}%</div>
            </div>
            <div className="kpi">
              <div className="text-slate-500 text-sm">Avg Duration</div>
              <div className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">{overview?.avgDurationSecs ? fmtDuration(overview!.avgDurationSecs) : '-'}</div>
            </div>
            <div className="kpi">
              <div className="text-slate-500 text-sm">Last Build</div>
              <div className="flex items-center gap-2 text-sm">
                <StatusBadge conclusion={overview?.lastBuild?.conclusion} />
                <a className="text-indigo-600 dark:text-indigo-400 underline" href={overview?.lastBuild?.url} target="_blank">Open</a>
              </div>
            </div>
          </div>
        )}

        {/* Charts */}
        <div className="grid gap-4">
          <div className="kpi">
            <div className="text-slate-700 dark:text-slate-200 font-semibold mb-2">Build Outcomes (by day)</div>
            <div style={{width:'100%', height:300}}>
              <ResponsiveContainer>
                <BarChart data={series}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="success" stackId="a" fill={successColor} />
                  <Bar dataKey="failure" stackId="a" fill={failureColor} />
                  <Bar dataKey="other"   stackId="a" fill={otherColor} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="kpi">
            <div className="text-slate-700 dark:text-slate-200 font-semibold mb-2">Average Duration (by day)</div>
            <div style={{width:'100%', height:300}}>
              <ResponsiveContainer>
                <LineChart data={series}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="avgDuration" stroke={lineColor} strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Runs table */}
        <div className="kpi">
          <div className="flex items-center justify-between mb-2">
            <div className="text-slate-700 dark:text-slate-200 font-semibold">Recent Runs</div>
            <button className="btn btn-primary" onClick={loadData}>Refresh now</button>
          </div>
          {error && <div className="mb-2 text-sm text-red-600">{error}</div>}
          <div className="overflow-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 dark:text-slate-400">
                  <th className="py-2">Run</th>
                  <th>Workflow</th>
                  <th>Repo</th>
                  <th>Branch</th>
                  <th>Status</th>
                  <th>Conclusion</th>
                  <th>Duration</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {runs.map(r => (
                  <tr key={r.id} className="border-t hover:bg-slate-50/60 dark:hover:bg-slate-800/60">
                    <td className="py-2">{r.id}</td>
                    <td>{r.workflow_name}</td>
                    <td>{r.repo}</td>
                    <td>{r.head_branch}</td>
                    <td><span className="badge bg-slate-100 dark:bg-slate-800">{r.status}</span></td>
                    <td><StatusBadge conclusion={r.conclusion} /></td>
                    <td>{fmtDuration(r.duration_secs)}</td>
                    <td className="space-x-2">
                      <a className="text-indigo-600 dark:text-indigo-400 underline" href={r.url} target="_blank">Open</a>
                      <button className="text-emerald-600 underline" onClick={()=>openRun(r)}>Details</button>
                    </td>
                  </tr>
                ))}
                {!runs.length && !loading && (
                  <tr><td colSpan={8} className="py-6 text-center text-slate-500">No runs found</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* Run details modal */}
      <Modal open={openDetails} onClose={()=>setOpenDetails(false)} title={selectedRun ? `Run ${selectedRun.id} • ${selectedRun.workflow_name}` : 'Run details'}>
        {selectedRun && (
          <div className="space-y-4">
            <div className="flex flex-wrap gap-3 text-sm">
              <div><span className="text-slate-500">Repo:</span> {selectedRun.repo}</div>
              <div><span className="text-slate-500">Branch:</span> {selectedRun.head_branch}</div>
              <div><span className="text-slate-500">Status:</span> {selectedRun.status}</div>
              <div><span className="text-slate-500">Conclusion:</span> {selectedRun.conclusion}</div>
              <div><span className="text-slate-500">Duration:</span> {fmtDuration(selectedRun.duration_secs)}</div>
              <a className="text-indigo-600 underline" href={selectedRun.url} target="_blank">Open in GitHub</a>
            </div>

            <div>
              <div className="font-semibold mb-2">Jobs</div>
              <div className="overflow-auto border rounded-xl">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-500">
                      <th className="py-2">Job</th>
                      <th>Status</th>
                      <th>Conclusion</th>
                      <th>Duration</th>
                    </tr>
                  </thead>
                  <tbody>
                    {jobs.map(j => (
                      <tr key={j.id} className="border-t">
                        <td className="py-2">{j.name}</td>
                        <td>{j.status}</td>
                        <td><StatusBadge conclusion={j.conclusion} /></td>
                        <td>{fmtDuration(j.duration_secs)}</td>
                      </tr>
                    ))}
                    {!jobs.length && (
                      <tr><td colSpan={4} className="py-6 text-center text-slate-500">No jobs found</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {jobLog && (
              <div>
                <div className="font-semibold mb-2">Log Snippet (last lines from first failed job)</div>
                <pre className="p-3 rounded-xl bg-slate-100 dark:bg-slate-800 overflow-auto max-h-72 text-xs whitespace-pre-wrap">{jobLog}</pre>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
