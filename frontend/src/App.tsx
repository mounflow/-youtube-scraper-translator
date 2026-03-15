import React, { useState, useEffect, useRef, useCallback } from 'react'

// Error Boundary component - catches React render errors
class ErrorBoundary extends React.Component<{children: React.ReactNode}, {hasError: boolean, error?: Error}> {
  constructor(props: {children: React.ReactNode}) {
    super(props)
    this.state = { hasError: false }
  }
  static getDerivedStateFromError(error: Error) {
    console.error('[ErrorBoundary] Caught error:', error)
    return { hasError: true, error }
  }
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('[ErrorBoundary] React Error:', error, errorInfo)
    console.error('[ErrorBoundary] Component stack:', errorInfo.componentStack)
  }
  handleReload = () => {
    this.setState({ hasError: false, error: undefined })
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '2rem',
          color: '#f87171',
          background: '#0f1117',
          minHeight: '100vh',
          fontFamily: 'system-ui, sans-serif'
        }}>
          <h2 style={{color: '#ef4444', marginBottom: '1rem'}}>⚠️ 页面出错了</h2>
          <div style={{marginBottom: '1rem', padding: '1rem', background: '#1f2937', borderRadius: '8px'}}>
            <p style={{fontWeight: 'bold', color: '#f87171'}}>错误信息:</p>
            <pre style={{
              fontSize: '12px',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              color: '#d1d5db',
              background: '#111827',
              padding: '1rem',
              borderRadius: '6px',
              overflow: 'auto',
              maxHeight: '200px'
            }}>{this.state.error?.message}</pre>
          </div>
          <div style={{marginBottom: '1rem', padding: '1rem', background: '#1f2937', borderRadius: '8px'}}>
            <p style={{fontWeight: 'bold', color: '#9ca3af'}}>错误堆栈:</p>
            <pre style={{
              fontSize: '10px',
              whiteSpace: 'pre-wrap',
              color: '#9ca3af',
              background: '#111827',
              padding: '1rem',
              borderRadius: '6px',
              overflow: 'auto',
              maxHeight: '200px'
            }}>{this.state.error?.stack}</pre>
          </div>
          <button
            onClick={this.handleReload}
            style={{
              marginTop: '1rem',
              padding: '10px 20px',
              fontSize: '14px',
              background: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            点击重试
          </button>
          <button
            onClick={() => window.location.reload()}
            style={{
              marginTop: '1rem',
              marginLeft: '1rem',
              padding: '10px 20px',
              fontSize: '14px',
              background: '#6b7280',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            刷新页面
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

// Global error handler for uncaught errors
if (typeof window !== 'undefined') {
  window.onerror = (message, source, lineno, colno, error) => {
    console.error('[Global Error]', { message, source, lineno, colno, error })
  }
  window.onunhandledrejection = (event) => {
    console.error('[Unhandled Promise Rejection]', event.reason)
  }
}

import {
  Search, Youtube, Play, Settings, Clock, Eye, Plus, Trash2,
  CheckSquare, Square, List,
  Mic, Sparkles, Combine, Type, X, Terminal, AlertCircle,
  CheckCircle2, Loader2, Circle, ExternalLink,
  ChevronDown, ChevronUp, Volume2, Layers,
  FolderOpen, RefreshCw, FileVideo
} from 'lucide-react'

// ─────────────────────────── Types ─────────────────────────────

interface VideoResult {
  id: string
  title: string
  url: string
  duration: string
  duration_sec: number
  views: string
  thumbnail: string
  channel: string
  upload_date: string
  description: string
}

interface TaskData {
  id: string
  title: string
  url: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'canceled'
  created_at: string
  started_at: string | null
  finished_at: string | null
  progress: number
  current_step: string
  output_file: string | null
  log_count: number
}

interface TaskCounts {
  total: number
  pending: number
  running: number
  success: number
  failed: number
}

interface QueueSettings {
  style: string
  dub: boolean
  voice: string
  smart_split: boolean
  hardware_accel: boolean
  no_optimize: boolean
  cookies_file: string
  subtitle_lang: string
}

interface Toast {
  id: string
  type: 'success' | 'error' | 'info'
  message: string
}

// ─────────────────────────── Constants ─────────────────────────

const API = ''  // Proxied via Vite
const OUTPUT_DIR = 'D:/AI_Practice/-youtube-scraper-translator/output'

const STEP_LABELS: Record<string, string> = {
  download: '下载视频',
  subtitle: '提取字幕',
  translate: 'AI翻译',
  burn: '烧录字幕',
  dub: '中文配音',
  done: '完成',
  failed: '失败',
}

const STEP_ORDER = ['download', 'subtitle', 'translate', 'burn', 'done']

// ─────────────────────────── Helpers ───────────────────────────

function StatusBadge({ status }: { status: TaskData['status'] }) {
  const cfgMap: Record<string, { cls: string; icon: React.ReactNode; label: string }> = {
    pending: { cls: 'status-pending', icon: <Circle size={10} />, label: '等待中' },
    running: { cls: 'status-running', icon: <Loader2 size={10} className="animate-spin" />, label: '处理中' },
    success: { cls: 'status-success', icon: <CheckCircle2 size={10} />, label: '已完成' },
    failed: { cls: 'status-failed', icon: <AlertCircle size={10} />, label: '失败' },
    canceled: { cls: 'status-canceled', icon: <X size={10} />, label: '已取消' },
  }
  const safeStatus = status || 'pending'
  const cfg = cfgMap[safeStatus] || { cls: 'status-pending', icon: null, label: safeStatus }

  return (
    <span className={`status-badge ${cfg.cls}`}>
      {cfg.icon} {cfg.label}
    </span>
  )
}

function StepIndicator({ step }: { step: string }) {
  const current = STEP_ORDER.indexOf(step)
  return (
    <div className="flex items-center gap-1 flex-wrap">
      {STEP_ORDER.filter(s => s !== 'done').map((s, i) => {
        const state = current < 0 ? 'future' : i < current ? 'done' : i === current ? 'active' : 'future'
        return (
          <div key={s} className="flex items-center gap-1">
            <div className={`step-dot step-${state}`} title={STEP_LABELS[s]} />
            {i < STEP_ORDER.length - 2 && <div className={`step-line ${state !== 'future' ? 'step-line-done' : ''}`} />}
          </div>
        )
      })}
    </div>
  )
}

// ─────────────────────────── Preview Modal ─────────────────────

function PreviewModal({ video, onClose, onAdd }: {
  video: VideoResult
  onClose: () => void
  onAdd: (v: VideoResult) => void
}) {
  const embedUrl = `https://www.youtube.com/embed/${video.id}?autoplay=1&rel=0`

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-box" onClick={e => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1 min-w-0 pr-4">
            <h2 className="text-xl font-bold text-white line-clamp-2 leading-snug">{video.title}</h2>
            <div className="flex items-center gap-4 mt-2 text-sm text-slate-400">
              <span className="flex items-center gap-1.5"><Clock size={14} /> {video.duration}</span>
              <span className="flex items-center gap-1.5"><Eye size={14} /> {video.views} 播放</span>
              <span className="text-blue-300 bg-blue-500/10 px-2 py-0.5 rounded text-xs">{video.channel}</span>
            </div>
          </div>
          <button onClick={onClose} className="icon-btn text-slate-400 hover:text-white flex-shrink-0 bg-white/5 p-2 rounded-full hover:bg-white/10 transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="w-full aspect-video rounded-2xl overflow-hidden bg-black mb-4 shadow-2xl relative">
          <iframe
            src={embedUrl}
            className="w-full h-full"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>

        {video.description && (
          <p className="text-sm text-slate-400 line-clamp-3 mb-4">{video.description}</p>
        )}

        <div className="flex items-center gap-3">
          <button
            onClick={() => { onAdd(video); onClose() }}
            className="btn-primary flex items-center gap-2 flex-1 justify-center"
          >
            <Plus size={16} /> 添加到队列
          </button>
          <a
            href={video.url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-ghost flex items-center gap-2"
          >
            <ExternalLink size={14} /> YouTube
          </a>
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────── Settings Panel ────────────────────

function SettingsPanel({ settings, onChange }: {
  settings: QueueSettings
  onChange: (s: QueueSettings) => void
}) {
  const [open, setOpen] = useState(false)

  const update = (patch: Partial<QueueSettings>) => onChange({ ...settings, ...patch })

  return (
    <div className="glass-panel rounded-2xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-white/5 transition-colors"
      >
        <span className="flex items-center gap-2 font-semibold text-sm">
          <Settings size={16} className="text-purple-400" /> 处理设置
        </span>
        {open ? <ChevronUp size={16} className="text-slate-400" /> : <ChevronDown size={16} className="text-slate-400" />}
      </button>

      {open && (
        <div className="px-5 pb-5 space-y-4 border-t border-white/10 pt-4">
          <div>
            <label className="settings-label"><Type size={13} className="text-purple-400" /> 字幕样式</label>
            <select
              value={settings.style}
              onChange={e => update({ style: e.target.value })}
              className="glass-input w-full rounded-xl px-3 py-2 text-sm text-white mt-1"
            >
              <option value="premium" className="text-black">Premium（推荐）</option>
              <option value="obama" className="text-black">Dynamic Default</option>
              <option value="box_classic" className="text-black">High Contrast Box</option>
            </select>
          </div>

          <div>
            <label className="settings-label"><Mic size={13} className="text-emerald-400" /> 中文配音</label>
            <div className="flex items-center gap-3 mt-1">
              <button
                onClick={() => update({ dub: !settings.dub })}
                className={`toggle ${settings.dub ? 'toggle-on' : 'toggle-off'}`}
              >
                <span className="toggle-thumb" />
              </button>
              <span className="text-sm text-slate-300">{settings.dub ? '启用' : '禁用'}</span>
            </div>
          </div>

          {settings.dub && (
            <div>
              <label className="settings-label"><Volume2 size={13} className="text-emerald-400" /> 配音声音</label>
              <select
                value={settings.voice}
                onChange={e => update({ voice: e.target.value })}
                className="glass-input w-full rounded-xl px-3 py-2 text-sm text-white mt-1"
              >
                <option value="zh-CN-YunxiNeural" className="text-black">云希（男声）</option>
                <option value="zh-CN-XiaoxiaoNeural" className="text-black">晓晓（女声）</option>
                <option value="zh-CN-YunyangNeural" className="text-black">云扬（男声 新闻）</option>
                <option value="zh-CN-XiaohanNeural" className="text-black">晓涵（女声）</option>
              </select>
            </div>
          )}

          <div className="space-y-3 pt-1">
            {[
              { key: 'smart_split', label: '音频智能分割', icon: <Combine size={13} className="text-amber-400" /> },
              { key: 'hardware_accel', label: 'NVENC 硬件加速', icon: <Sparkles size={13} className="text-cyan-400" /> },
              { key: 'no_optimize', label: '禁用AI翻译优化', icon: <Layers size={13} className="text-rose-400" /> },
            ].map(({ key, label, icon }) => (
              <label key={key} className="flex items-center gap-3 cursor-pointer group">
                <button
                  onClick={() => update({ [key]: !settings[key as keyof QueueSettings] } as Partial<QueueSettings>)}
                  className={`toggle ${settings[key as keyof QueueSettings] ? 'toggle-on' : 'toggle-off'}`}
                >
                  <span className="toggle-thumb" />
                </button>
                <span className="settings-label flex items-center gap-1.5 mb-0">{icon} {label}</span>
              </label>
            ))}
          </div>

          <div>
            <label className="settings-label">字幕语言</label>
            <select
              value={settings.subtitle_lang}
              onChange={e => update({ subtitle_lang: e.target.value })}
              className="glass-input w-full rounded-xl px-3 py-2 text-sm text-white mt-1"
            >
              <option value="en">英语 (English)</option>
              <option value="zh-CN">中文 (Chinese)</option>
              <option value="ja">日语 (Japanese)</option>
              <option value="ko">韩语 (Korean)</option>
              <option value="zh-TW">繁体中文</option>
              <option value="auto">自动检测</option>
            </select>
          </div>

          <div>
            <label className="settings-label">Cookies 文件</label>
            <input
              type="text"
              value={settings.cookies_file}
              onChange={e => update({ cookies_file: e.target.value })}
              placeholder="cookies.txt"
              className="glass-input w-full rounded-xl px-3 py-2 text-sm text-white mt-1"
            />
          </div>
        </div>
      )}
    </div>
  )
}

// ─────────────────────────── Log Panel ─────────────────────────

function LogPanel({ task, onClose }: { task: TaskData | null; onClose: () => void }) {
  const [logs, setLogs] = useState<string[]>([])
  const [snapTask, setSnapTask] = useState<TaskData | null>(null)
  const logEndRef = useRef<HTMLDivElement>(null)
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (esRef.current) {
      esRef.current.close()
      esRef.current = null
    }
    setLogs([])
    setSnapTask(task)
    if (!task) return

    // 如果任务不是 running 状态，显示提示但不连接 SSE
    if (task.status !== 'running') {
      setLogs([`任务状态: ${task.status === 'pending' ? '等待启动' : task.status === 'success' ? '已完成' : task.status === 'failed' ? '已失败' : '已取消'}`])
      return
    }

    const es = new EventSource(`${API}/api/tasks/${task.id}/stream`)
    esRef.current = es

    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.type === 'log') {
          setLogs(prev => [...prev, data.line])
        }
        if (data.type === 'status') {
          setSnapTask(prev => prev ? { ...prev, status: data.status, progress: data.progress, current_step: data.step, output_file: data.output_file } : prev)
        }
        if (['success', 'failed', 'canceled'].includes(data.status)) {
          es.close()
        }
      } catch { /* ignore parse errors */ }
    }
    es.onerror = () => es.close()

    return () => { es.close() }
  }, [task?.id])

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const lineColor = (line: string) => {
    if (line.includes('[ERROR]') || line.includes('Error') || line.includes('failed')) return 'text-red-400'
    if (line.includes('[DONE]') || line.includes('complete') || line.includes('✓')) return 'text-emerald-400'
    if (line.includes('[Step') || line.includes('Processing')) return 'text-blue-300'
    if (line.includes('%')) return 'text-amber-300'
    return 'text-slate-300'
  }

  return (
    <div className="log-panel flex flex-col h-full">
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/10 flex-shrink-0">
        <div className="flex items-center gap-2">
          <Terminal size={16} className="text-emerald-400" />
          <span className="font-semibold text-sm text-white">实时日志</span>
          {snapTask && <StatusBadge status={snapTask.status} />}
        </div>
        <button
          onClick={() => { onClose(); }}
          className="icon-btn text-slate-400 hover:text-white p-2 rounded-full hover:bg-white/10 transition-colors cursor-pointer"
          style={{ cursor: 'pointer', zIndex: 9999, position: 'relative', pointerEvents: 'auto' }}
        >
          <X size={18} />
        </button>
      </div>

      {!task ? (
        <div className="flex-1 flex flex-col items-center justify-center text-slate-500 gap-3">
          <Terminal size={32} />
          <p className="text-sm">点击任务的"日志"按钮查看实时输出</p>
        </div>
      ) : (
        <>
          {snapTask && (
            <div className="px-5 py-3 border-b border-white/5 flex-shrink-0 space-y-2">
              <p className="text-xs text-slate-400 font-medium line-clamp-1" title={snapTask.title}>{snapTask.title}</p>
              <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${snapTask.status === 'success' ? 'bg-emerald-500' :
                    snapTask.status === 'failed' ? 'bg-red-500' :
                      'bg-gradient-to-r from-blue-500 to-violet-500'
                    }`}
                  style={{ width: `${snapTask.progress > 0 ? snapTask.progress : (snapTask.status === 'running' ? 5 : (snapTask.status === 'success' ? 100 : 0))}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-xs text-slate-500">
                <StepIndicator step={snapTask.current_step} />
                <span>{snapTask.progress > 0 ? `${snapTask.progress.toFixed(1)}%` : ''}</span>
              </div>
            </div>
          )}

          <div className="flex-1 overflow-y-auto p-4 font-mono text-xs space-y-0.5">
            {logs.length === 0 && (
              <div className="text-slate-600 flex items-center gap-2 pt-4 justify-center">
                <Loader2 size={14} className="animate-spin" /> 等待输出...
              </div>
            )}
            {logs.map((line, i) => (
              <div key={i} className={`log-line ${lineColor(line)}`}>{line}</div>
            ))}
            <div ref={logEndRef} />
          </div>
        </>
      )}
    </div>
  )
}

// ─────────────────────────── Task Queue ────────────────────────

function TaskQueue({
  tasks, selected, counts,
  onSelect, onSelectAll,
  onStart, onDelete, onViewLog,
  onBatchStart, onBatchDelete,
  activeLogTaskId,
}: {
  tasks: TaskData[]
  selected: Set<string>
  counts: TaskCounts
  onSelect: (id: string) => void
  onSelectAll: () => void
  onStart: (id: string) => void
  onDelete: (id: string) => void
  onViewLog: (task: TaskData) => void
  onBatchStart: () => void
  onBatchDelete: () => void
  activeLogTaskId: string | null
}) {
  const safeTasks = tasks || []
  const allSelected = safeTasks.length > 0 && selected.size === safeTasks.length
  const someSelected = selected.size > 0

  return (
    <div className="glass-panel rounded-2xl flex flex-col overflow-hidden h-full">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-white/10 flex-shrink-0">
        <List size={15} className="text-blue-400" />
        <h2 className="font-semibold text-sm flex-1 text-white">任务队列</h2>
        <div className="flex items-center gap-1.5">
          <span className="stat-chip stat-pending">{(counts?.pending) || 0} 等待</span>
          <span className="stat-chip stat-running">{(counts?.running) || 0} 运行</span>
          <span className="stat-chip stat-success">{(counts?.success) || 0} 完成</span>
          {(counts?.failed) > 0 && <span className="stat-chip stat-failed">{counts.failed} 失败</span>}
        </div>
      </div>

      {/* Bulk Actions */}
      {safeTasks.length > 0 && (
        <div className="flex items-center gap-2 px-4 py-2.5 border-b border-white/5 bg-white/2 flex-shrink-0">
          <button onClick={onSelectAll} className="icon-btn text-slate-400 hover:text-white">
            {allSelected ? <CheckSquare size={15} className="text-blue-400" /> : <Square size={15} />}
          </button>
          <span className="text-xs text-slate-500 flex-1">
            {someSelected ? `已选 ${selected.size} / ${safeTasks.length}` : `共 ${safeTasks.length} 个任务`}
          </span>
          {someSelected && (
            <>
              <button
                onClick={onBatchStart}
                className="bulk-btn bulk-start flex items-center gap-1"
              >
                <Play size={11} className="fill-current" /> 启动已选
              </button>
              <button
                onClick={onBatchDelete}
                className="bulk-btn bulk-delete flex items-center gap-1"
              >
                <Trash2 size={11} /> 删除已选
              </button>
            </>
          )}
        </div>
      )}

      {/* Task List */}
      <div className="flex-1 overflow-y-auto">
        {!tasks || tasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-600 gap-3 py-16">
            <List size={32} />
            <p className="text-sm text-center">队列为空<br /><span className="text-xs text-slate-700">从左侧搜索并添加视频</span></p>
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {safeTasks.filter(t => t && t.id).map(task => (
              <div
                key={task.id}
                className={`task-row ${selected.has(task.id) ? 'task-row-selected' : ''} ${activeLogTaskId === task.id ? 'task-row-active' : ''}`}
              >
                <button
                  onClick={() => onSelect(task.id)}
                  className="flex-shrink-0 icon-btn text-slate-500 hover:text-slate-200"
                >
                  {selected.has(task.id)
                    ? <CheckSquare size={15} className="text-blue-400" />
                    : <Square size={15} />}
                </button>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <StatusBadge status={task.status || 'pending'} />
                    {task.status === 'running' && (
                      <div className="flex-1 max-w-[80px] h-1 rounded-full bg-white/10 overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-blue-500 to-violet-500 transition-all duration-500"
                          style={{ width: `${(task.progress || 0) > 0 ? task.progress : 5}%` }}
                        />
                      </div>
                    )}
                  </div>
                  <p className="text-xs text-slate-200 font-medium line-clamp-1" title={task.title || ''}>
                    {task.title || '未知任务'}
                  </p>
                  <p className="text-xs text-slate-600 mt-0.5">
                    {task.status === 'running' && task.current_step ? STEP_LABELS[task.current_step] ?? task.current_step :
                      task.status === 'success' && task.output_file ? `✓ ${task.output_file}` :
                        task.created_at ? new Date(task.created_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : ''
                    }
                  </p>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-0.5 flex-shrink-0">
                  {(task.status === 'pending' || task.status === 'failed' || task.status === 'canceled') && (
                    <button
                      onClick={(e) => onStart(task.id, e)}
                      className="action-btn action-start"
                      title="启动"
                    >
                      <Play size={12} className="fill-current" />
                    </button>
                  )}
                  <button
                    onClick={() => task && onViewLog(task)}
                    className={`action-btn action-log ${activeLogTaskId === task.id ? 'action-log-active' : ''}`}
                    title="查看日志"
                  >
                    <Terminal size={12} />
                  </button>
                  <button
                    onClick={() => onDelete(task.id)}
                    className="action-btn action-delete"
                    title="删除"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────── Output Files View ──────────────────────

interface OutputFile {
  name: string
  size_mb: number
  modified: string
}

function OutputFilesView({ onViewLog }: { onViewLog: (task: TaskData) => void }) {
  const [files, setFiles] = useState<OutputFile[]>([])
  const [isLoading, setIsLoading] = useState(true)

  const fetchFiles = useCallback(async () => {
    setIsLoading(true)
    try {
      const res = await fetch(`${API}/api/files/output`)
      const data = await res.json()
      setFiles(data.files || [])
    } catch {
      console.error('Failed to fetch output files')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchFiles()
    // 定时刷新
    const interval = setInterval(fetchFiles, 5000)
    return () => clearInterval(interval)
  }, [fetchFiles])

  const handleOpenFolder = (filename: string) => {
    // 打开文件所在文件夹
    window.open(`file:///${OUTPUT_DIR}/${filename}`, '_blank')
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <FolderOpen size={20} className="text-green-400" /> 输出文件
        </h2>
        <button onClick={fetchFiles} className="btn-secondary text-sm">
          <RefreshCw size={14} className="mr-1" /> 刷新
        </button>
      </div>

      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <Loader2 size={24} className="animate-spin text-blue-400" />
        </div>
      ) : files.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-slate-400">
          <div className="text-center">
            <FolderOpen size={48} className="mx-auto mb-2 opacity-50" />
            <p>暂无输出文件</p>
            <p className="text-xs mt-1">处理任务完成后会自动显示在这里</p>
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-2">
          {files.map((file) => (
            <div
              key={file.name}
              className="glass-panel rounded-xl p-3 flex items-center gap-3 hover:bg-white/5 transition-colors"
            >
              <FileVideo size={20} className="text-blue-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white truncate">{file.name}</p>
                <p className="text-xs text-slate-400">
                  {file.size_mb} MB • {new Date(file.modified).toLocaleString('zh-CN')}
                </p>
              </div>
              <button
                onClick={() => handleOpenFolder(file.name)}
                className="btn-secondary text-xs px-2 py-1"
                title="打开文件夹"
              >
                <FolderOpen size={12} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────── Search Panel ──────────────────────

function SearchPanel({
  onAddToQueue,
  settings,
  onSettingsChange,
  addToast,
  fetchTasks,
}: {
  onAddToQueue: (video: VideoResult) => void
  settings: QueueSettings
  onSettingsChange: (s: QueueSettings) => void
  addToast?: (type: 'success' | 'error' | 'info', message: string) => void
  fetchTasks?: () => void
}) {
  const [query, setQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)
  const [results, setResults] = useState<VideoResult[]>([])
  const [error, setError] = useState('')
  const [durationMin, setDurationMin] = useState(60)
  const [durationMax, setDurationMax] = useState(7200)
  const [noFilter, setNoFilter] = useState(false)
  const [previewVideo, setPreviewVideo] = useState<VideoResult | null>(null)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    setIsSearching(true)
    setHasSearched(true)
    setError('')
    setResults([])

    try {
      const res = await fetch(`${API}/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query.trim(),
          duration_min: durationMin,
          duration_max: durationMax,
          max_results: 10,
          no_filter: noFilter,
          cookies_file: settings.cookies_file,
        }),
      })
      const data = await res.json()
      if (data.status === 'success') {
        setResults(data.results)
        if (data.results.length === 0) setError('没有找到匹配的视频，请尝试其他关键词')
      } else {
        setError(data.message || '搜索失败')
      }
    } catch {
      setError('无法连接到后端服务，请确认 server.py 已启动')
    } finally {
      setIsSearching(false)
    }
  }

  const [urlInput, setUrlInput] = useState('')
  const [isAddingUrl, setIsAddingUrl] = useState(false)

  // 直接添加URL到队列
  const handleAddUrl = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!urlInput.trim()) return

    // 简单解析YouTube URL获取视频ID
    let videoUrl = urlInput.trim()
    let videoId = ''
    let videoTitle = 'YouTube Video'

    // 支持多种YouTube URL格式
    const patterns = [
      /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})/,
      /^([a-zA-Z0-9_-]{11})$/  // 直接输入11位视频ID
    ]

    for (const pattern of patterns) {
      const match = videoUrl.match(pattern)
      if (match) {
        videoId = match[1]
        break
      }
    }

    if (!videoId) {
      setError('请输入有效的YouTube链接或视频ID')
      return
    }

    videoUrl = `https://www.youtube.com/watch?v=${videoId}`

    setIsAddingUrl(true)
    setError('')

    try {
      const res = await fetch(`${API}/api/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: videoTitle,
          url: videoUrl,
          thumbnail: `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`,
          ...settings,
        }),
      })
      const data = await res.json()
      if (data.status === 'created') {
        addToast('success', `已添加视频到队列`)
        fetchTasks?.()
        setUrlInput('')
      } else {
        setError(data.message || '添加失败')
      }
    } catch {
      setError('无法连接到后端服务')
    } finally {
      setIsAddingUrl(false)
    }
  }

  return (
    <div className="flex flex-col gap-4 h-full overflow-hidden">
      {/* Direct URL Input */}
      <div className="glass-panel rounded-2xl p-4 flex-shrink-0">
        <h2 className="flex items-center gap-2 font-semibold text-sm mb-3">
          <ExternalLink size={15} className="text-green-400" /> 直接添加链接
        </h2>
        <form onSubmit={handleAddUrl} className="space-y-2">
          <input
            type="text"
            placeholder="粘贴 YouTube 链接或视频ID"
            value={urlInput}
            onChange={e => setUrlInput(e.target.value)}
            className="glass-input w-full rounded-xl px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:ring-1 focus:ring-green-500/50"
          />
          <button
            type="submit"
            disabled={isAddingUrl || !urlInput.trim()}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {isAddingUrl
              ? <><Loader2 size={14} className="animate-spin" /> 添加中...</>
              : <><Plus size={14} /> 直接添加</>}
          </button>
        </form>
        {error && <p className="text-xs text-red-400 mt-2">{error}</p>}
      </div>

      {/* Search Form */}
      <div className="glass-panel rounded-2xl p-4 flex-shrink-0">
        <h2 className="flex items-center gap-2 font-semibold text-sm mb-3">
          <Search size={15} className="text-blue-400" /> 搜索视频
        </h2>
        <form onSubmit={handleSearch} className="space-y-3">
          <input
            type="text"
            placeholder="输入关键词，例如：AI tutorial"
            value={query}
            onChange={e => setQuery(e.target.value)}
            className="glass-input w-full rounded-xl px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:ring-1 focus:ring-blue-500/50"
          />

          {!noFilter && (
            <div className="flex items-center gap-2">
              <div className="flex-1">
                <label className="settings-label">最短时长（秒）</label>
                <input
                  type="number"
                  value={durationMin}
                  onChange={e => setDurationMin(Number(e.target.value))}
                  className="glass-input w-full rounded-xl px-3 py-1.5 text-sm text-white mt-1"
                />
              </div>
              <div className="flex-1">
                <label className="settings-label">最长时长（秒）</label>
                <input
                  type="number"
                  value={durationMax}
                  onChange={e => setDurationMax(Number(e.target.value))}
                  className="glass-input w-full rounded-xl px-3 py-1.5 text-sm text-white mt-1"
                />
              </div>
            </div>
          )}

          <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-400">
            <button
              type="button"
              onClick={() => setNoFilter(!noFilter)}
              className={`toggle ${noFilter ? 'toggle-on' : 'toggle-off'}`}
            >
              <span className="toggle-thumb" />
            </button>
            不限制时长
          </label>

          <button
            type="submit"
            disabled={isSearching}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {isSearching
              ? <><Loader2 size={14} className="animate-spin" /> 搜索中...</>
              : <><Search size={14} /> 搜索</>}
          </button>
        </form>
        {error && <p className="mt-2 text-xs text-red-400">{error}</p>}
      </div>

      {/* Settings */}
      <div className="flex-shrink-0">
        <SettingsPanel settings={settings} onChange={onSettingsChange} />
      </div>

      {/* Results */}
      {!isSearching && !hasSearched && results.length === 0 && (
        <div className="flex flex-col items-center justify-center flex-1 text-slate-400 mt-10">
          <Youtube size={48} className="mb-4 opacity-20" />
          <p className="text-sm">👆 请在上方输入关键词开始搜索</p>
        </div>
      )}
      {!isSearching && hasSearched && results.length === 0 && !error && (
        <div className="flex flex-col items-center justify-center flex-1 text-slate-400 mt-10">
          <Search size={48} className="mb-4 opacity-20" />
          <p className="text-sm">未找到相关视频，尝试开启"不限制时长"</p>
        </div>
      )}
      {results.length > 0 && (
        <div className="flex-1 overflow-y-auto space-y-3 pr-1">
          <p className="text-xs text-slate-500 px-1">找到 {results.length} 个视频</p>
          {results.map(video => (
            <div key={video.id} className="video-card group">
              <div className="relative aspect-video rounded-xl overflow-hidden bg-black/40 flex-shrink-0 w-28">
                <img
                  src={video.thumbnail}
                  alt={video.title}
                  className="w-full h-full object-cover"
                  onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
                />
                <div className="absolute bottom-1 right-1 bg-black/80 rounded px-1.5 py-0.5 text-xs font-mono">
                  {video.duration}
                </div>
              </div>

              <div className="flex-1 min-w-0 flex flex-col justify-between py-0.5">
                <div>
                  <p className="text-sm font-medium text-slate-100 line-clamp-2 leading-snug" title={video.title}>
                    {video.title}
                  </p>
                  <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
                    <Eye size={10} /> {video.views}
                    <span className="truncate max-w-[80px]">{video.channel}</span>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 mt-2">
                  <button
                    onClick={() => setPreviewVideo(video)}
                    className="btn-ghost text-xs flex items-center gap-1 py-1"
                  >
                    <Play size={10} className="fill-current" /> 预览
                  </button>
                  <button
                    onClick={() => onAddToQueue(video)}
                    className="btn-primary text-xs flex items-center gap-1 py-1 flex-1 justify-center"
                  >
                    <Plus size={10} /> 加入队列
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Preview Modal */}
      {previewVideo && (
        <PreviewModal
          video={previewVideo}
          onClose={() => setPreviewVideo(null)}
          onAdd={onAddToQueue}
        />
      )}
    </div>
  )
}

// ─────────────────────────── Toast ─────────────────────────────

function ToastContainer({ toasts, onRemove }: { toasts: Toast[]; onRemove: (id: string) => void }) {
  return (
    <div className="toast-container">
      {toasts.map(t => (
        <div key={t.id} className={`toast toast-${t.type}`} onClick={() => onRemove(t.id)}>
          {t.type === 'success' && <CheckCircle2 size={14} />}
          {t.type === 'error' && <AlertCircle size={14} />}
          <span>{t.message}</span>
        </div>
      ))}
    </div>
  )
}

// ─────────────────────────── Main App ──────────────────────────

type AppView = 'search' | 'queue' | 'output'

export default function App() {
  const [view, setView] = useState<AppView>('queue')
  const [tasks, setTasksList] = useState<TaskData[]>([])
  const [counts, setCounts] = useState<TaskCounts>({ total: 0, pending: 0, running: 0, success: 0, failed: 0 })
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [activeLogTask, setActiveLogTask] = useState<TaskData | null>(null)
  const [toasts, setToasts] = useState<Toast[]>([])

  const handleSetView = useCallback((newView: AppView) => {
    setView(newView)
  }, [])

  const [settings, setSettings] = useState<QueueSettings>({
    style: 'premium',
    dub: false,
    voice: 'zh-CN-YunxiNeural',
    smart_split: true,
    hardware_accel: true,
    no_optimize: false,
    cookies_file: 'cookies.txt',
    subtitle_lang: 'en',
  })

  const prevStatusRef = useRef<Record<string, string>>({})
  const activeLogTaskRef = useRef<TaskData | null>(null)
  const userClosedLogPanelRef = useRef(false)

  // Keep ref in sync without causing fetchTasks to re-create
  useEffect(() => { activeLogTaskRef.current = activeLogTask }, [activeLogTask])

  const addToast = useCallback((type: Toast['type'], message: string) => {
    const id = Math.random().toString(36).slice(2)
    setToasts(prev => [...prev, { id, type, message }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000)
  }, [])

  // Poll task list every 3s
  const fetchTasks = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/tasks`)
      const data = await res.json()
      const taskList: TaskData[] = data.tasks ?? []
      const newCounts: TaskCounts = data.counts ?? { total: 0, pending: 0, running: 0, success: 0, failed: 0 }

      // Check for status transitions → toast
      const prevStatus = prevStatusRef.current
      taskList.forEach(t => {
        if (!t || !t.id || !t.status) return // Skip invalid tasks
        const old = prevStatus[t.id]
        if (old && old !== t.status) {
          const title = t.title || '未知任务'
          if (t.status === 'success') addToast('success', `✓ 完成: ${title.slice(0, 30)}...`)
          if (t.status === 'failed') addToast('error', `✗ 失败: ${title.slice(0, 30)}...`)
        }
        prevStatus[t.id] = t.status
      })
      prevStatusRef.current = prevStatus

      setTasksList(taskList)
      setCounts(newCounts)

      // Update active log task snapshot (via ref to avoid stale closure)
      // Only update if activeLogTask is not null (user hasn't closed the panel)
      const current = activeLogTaskRef.current
      if (current) {
        const updated = taskList.find(t => t.id === current.id)
        if (updated && !userClosedLogPanelRef.current) setActiveLogTask(updated)
      }
    } catch { /* server might not be up yet */ }
  }, [addToast])  // stable: no longer depends on activeLogTask

  useEffect(() => {
    fetchTasks()
    const interval = setInterval(fetchTasks, 3000)
    return () => clearInterval(interval)
  }, [fetchTasks])

  const handleAddToQueue = useCallback(async (video: VideoResult) => {
    try {
      const res = await fetch(`${API}/api/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: video.title,
          url: video.url,
          thumbnail: video.thumbnail,
          ...settings,
        }),
      })
      const data = await res.json()
      if (data.status === 'created') {
        addToast('success', `已添加到队列: ${video.title.slice(0, 30)}...`)
        fetchTasks()
        // 不再自动跳转，让用户停留在当前页面
      }
    } catch {
      addToast('error', '添加失败，请检查后端连接')
    }
  }, [settings, addToast, fetchTasks])

  const handleStart = useCallback(async (id: string, e?: React.MouseEvent) => {
    e?.preventDefault?.()
    e?.stopPropagation?.()
    await fetch(`${API}/api/tasks/${id}/start`, { method: 'POST' })
    fetchTasks()
  }, [fetchTasks])

  const handleDelete = useCallback(async (id: string) => {
    await fetch(`${API}/api/tasks/${id}`, { method: 'DELETE' })
    setSelected(prev => { const s = new Set(prev); s.delete(id); return s })
    if (activeLogTask?.id === id) setActiveLogTask(null)
    fetchTasks()
  }, [fetchTasks, activeLogTask])

  const handleViewLog = useCallback((task: TaskData) => {
    userClosedLogPanelRef.current = false
    setActiveLogTask(task)
  }, [])

  const handleBatchStart = useCallback(async () => {
    await fetch(`${API}/api/tasks/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_ids: [...selected], action: 'start' }),
    })
    setSelected(new Set())
    fetchTasks()
  }, [selected, fetchTasks])

  const handleBatchDelete = useCallback(async () => {
    await fetch(`${API}/api/tasks/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_ids: [...selected], action: 'delete' }),
    })
    setSelected(new Set())
    if (activeLogTask && selected.has(activeLogTask.id)) setActiveLogTask(null)
    fetchTasks()
  }, [selected, fetchTasks, activeLogTask])

  const handleSelect = useCallback((id: string) => {
    setSelected(prev => {
      const s = new Set(prev)
      s.has(id) ? s.delete(id) : s.add(id)
      return s
    })
  }, [])

  const handleSelectAll = useCallback(() => {
    const safeTasks = tasks || []
    if (selected.size === safeTasks.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(safeTasks.map(t => t.id).filter(Boolean)))
    }
  }, [tasks, selected])

  return (
    <ErrorBoundary>
    <div className="app-shell">
      {/* ── Header ── */}
      <header className="app-header">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-red-500/20 rounded-xl border border-red-500/30">
            <Youtube size={22} className="text-red-500" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-red-400 to-rose-300">
              YT Localizer Pro
            </h1>
            <p className="text-xs text-slate-500">YouTube 视频本地化工作站</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-3 text-xs text-slate-400">
            {(counts?.running ?? 0) > 0 && (
              <span className="flex items-center gap-1.5 text-blue-400 animate-pulse-slow">
                <Loader2 size={12} className="animate-spin" /> {counts?.running ?? 0} 处理中
              </span>
            )}
            <span className="flex items-center gap-1.5">
              <CheckCircle2 size={12} className="text-emerald-400" /> {counts?.success ?? 0} 已完成
            </span>
            <span className="flex items-center gap-1.5">
              <Circle size={12} className="text-slate-500" /> {counts?.pending ?? 0} 等待中
            </span>
          </div>

          <div className="flex bg-white/5 rounded-lg p-1 border border-white/10 ml-4">
            <button onClick={() => handleSetView('search')} className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${view === 'search' ? 'bg-white/10 text-white shadow-sm' : 'text-slate-400 hover:text-slate-300'}`}>🔍 发现</button>
            <button onClick={() => handleSetView('queue')} className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${view === 'queue' ? 'bg-white/10 text-white shadow-sm' : 'text-slate-400 hover:text-slate-300'}`}>⚙️ 处理</button>
            <button onClick={() => handleSetView('output')} className={`hidden lg:block px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${view === 'output' ? 'bg-white/10 text-white shadow-sm' : 'text-slate-400 hover:text-slate-300'}`}>📁 输出</button>
          </div>
        </div>
      </header>

      {/* ── Dynamic Layout ── */}
      {view === 'output' ? (
        /* Output Files View */
        <main className="app-main view-output">
          <section className="col-output">
            <OutputFilesView onViewLog={handleViewLog} />
          </section>
        </main>
      ) : (
      /* 搜索 + 任务队列 分屏显示 */
      <main className="app-main view-split">
        {/* LEFT: Search + Settings */}
        <aside className="col-search">
          <SearchPanel
            onAddToQueue={handleAddToQueue}
            settings={settings}
            onSettingsChange={setSettings}
            addToast={addToast}
            fetchTasks={fetchTasks}
          />
        </aside>

        {/* CENTER: Task Queue */}
        <section className="col-queue">
          <TaskQueue
            tasks={tasks}
            selected={selected}
            counts={counts}
            onSelect={handleSelect}
            onSelectAll={handleSelectAll}
            onStart={handleStart}
            onDelete={handleDelete}
            onViewLog={handleViewLog}
            onBatchStart={handleBatchStart}
            onBatchDelete={handleBatchDelete}
            activeLogTaskId={activeLogTask?.id ?? null}
          />
        </section>

        {/* RIGHT: Log Panel */}
        {activeLogTask && (
        <section className="col-logs">
          <LogPanel task={activeLogTask} onClose={() => { console.log('Closing panel...'); userClosedLogPanelRef.current = true; setActiveLogTask(null); }} />
        </section>
        )}
      </main>
      )}

      {/* Toasts */}
      <ToastContainer toasts={toasts} onRemove={id => setToasts(p => p.filter(t => t.id !== id))} />
    </div>
    </ErrorBoundary>
  )
}
