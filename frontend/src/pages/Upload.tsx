import { useState, useRef, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ACCOUNT_OPTIONS } from '../accounts'
import type { ClassifyQuestion, WsMessage } from '../types'

interface LogLine {
  text: string
  type: 'info' | 'ok' | 'warn' | 'question'
}

export default function Upload() {
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [account, setAccount] = useState('211')
  const [dragging, setDragging] = useState(false)
  const [running, setRunning] = useState(false)
  const [progress, setProgress] = useState<{ index: number; total: number } | null>(null)
  const [question, setQuestion] = useState<ClassifyQuestion | null>(null)
  const [optionSearch, setOptionSearch] = useState('')
  const [logs, setLogs] = useState<LogLine[]>([])
  const wsRef = useRef<WebSocket | null>(null)
  const logEndRef = useRef<HTMLDivElement | null>(null)

  // Auto-scroll log to bottom
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const addLog = (text: string, type: LogLine['type'] = 'info') => {
    setLogs((prev) => [...prev, { text, type }])
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f?.name.endsWith('.csv')) setFile(f)
  }, [])

  const handleAnswer = (category: string) => {
    wsRef.current?.send(JSON.stringify({ type: 'answer', category }))
    addLog(`  → You chose: ${category}`, 'ok')
    setQuestion(null)
    setOptionSearch('')
  }

  const startClassification = async () => {
    if (!file) return
    setRunning(true)
    setLogs([])

    addLog(`📂 Reading: ${file.name}`)
    addLog(`🏦 Account: ${account}`)
    addLog('─'.repeat(52))

    const form = new FormData()
    form.append('file', file)
    form.append('account', account)
    const res = await fetch('/api/classify', { method: 'POST', body: form })
    const { session_id } = await res.json()

    const wsBase = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000'
    const ws = new WebSocket(`${wsBase}/ws/${session_id}`)
    wsRef.current = ws

    ws.onmessage = (e) => {
      const msg: WsMessage = JSON.parse(e.data)

      if (msg.type === 'progress') {
        const tx = msg.transaction
        const conf = tx.confidence === 'high' ? '✅' : tx.confidence === 'medium' ? '🟡' : '❓'
        const src = ({ hist: 'hist', kw: 'kw', ai: 'ai', user: 'user' } as Record<string, string>)[tx.method] ?? '?'
        const cat = tx.category_label ? `${tx.category} ${tx.category_label}` : tx.category
        addLog(
          `[${msg.index}/${msg.total}] ${tx.date} | ${tx.description.slice(0, 38).padEnd(38)} | ${tx.amount.toFixed(2).padStart(9)} €  ${conf} [${src}] ${cat}`,
          'ok',
        )
        setProgress({ index: msg.index, total: msg.total })

      } else if (msg.type === 'question') {
        setProgress({ index: msg.index, total: msg.total })
        const tx = msg.transaction
        addLog(`  🤔 Unsure: "${tx.description}" (${tx.amount.toFixed(2)} €)`, 'question')
        addLog(`     AI suggests: ${msg.suggestion} — ${msg.reason}`, 'warn')
        setQuestion(msg)

      } else if (msg.type === 'done') {
        addLog('─'.repeat(52))
        addLog(`✅ Done — ${msg.results.length} transactions classified`)
        const dups = msg.duplicates ?? []
        if (dups.length > 0) {
          addLog(`⚠️  ${dups.length} duplicate${dups.length === 1 ? '' : 's'} already in staging (pending upload to Sheets):`, 'warn')
          for (const d of dups) {
            addLog(`   ${d.date} | ${d.description.slice(0, 38)} | ${d.amount.toFixed(2)} €`, 'warn')
          }
          addLog('   These will NOT be added to staging again to avoid double-counting.', 'warn')
        }
        ws.close()
        setTimeout(
          () => navigate('/dashboard'),
          dups.length > 0 ? 2500 : 800,
        )
      }
    }

    ws.onerror = () => addLog('❌ WebSocket error — is the backend running?', 'warn')
  }

  const pct = progress ? Math.round((progress.index / progress.total) * 100) : 0

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col items-center p-6 gap-6">

      {/* Header */}
      <div className="flex items-center justify-between w-full pt-4">
        <div>
          <h1 className="text-3xl font-semibold text-white">💰 PnL AI</h1>
          <p className="text-gray-400 mt-1 text-sm">Upload your bank CSV to categorize transactions</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => navigate('/dashboard')} className="px-3 py-1.5 rounded-lg border border-gray-700 text-gray-400 text-xs hover:border-gray-500 transition-colors">
            📊 Dashboard
          </button>
          <button onClick={() => navigate('/manual')} className="px-3 py-1.5 rounded-lg border border-gray-700 text-gray-400 text-xs hover:border-gray-500 transition-colors">
            ✍ Manual
          </button>
          <button onClick={() => navigate('/history')} className="px-3 py-1.5 rounded-lg border border-gray-700 text-gray-400 text-xs hover:border-gray-500 transition-colors">
            📚 History
          </button>
          <button onClick={() => navigate('/categories')} className="px-3 py-1.5 rounded-lg border border-gray-700 text-gray-400 text-xs hover:border-gray-500 transition-colors">
            🗂 Categories
          </button>
        </div>
      </div>

      {/* Top panel — upload controls or question card */}
      <div className="w-full max-w-2xl space-y-4">
        {!running && (
          <>
            {/* Drop zone */}
            <div
              onDrop={handleDrop}
              onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              onClick={() => document.getElementById('file-input')?.click()}
              className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors
                ${dragging
                  ? 'border-indigo-400 bg-indigo-950'
                  : 'border-gray-700 bg-gray-900 hover:border-indigo-500'}`}
            >
              <input
                id="file-input"
                type="file"
                accept=".csv"
                className="hidden"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
              {file ? (
                <p className="text-indigo-300 font-medium">📄 {file.name}</p>
              ) : (
                <>
                  <p className="text-4xl mb-2">📂</p>
                  <p className="text-gray-400">Drag & drop a CSV, or click to browse</p>
                </>
              )}
            </div>

            {/* Account selector */}
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1 uppercase tracking-wide">
                Asset account
              </label>
              <select
                value={account}
                onChange={(e) => setAccount(e.target.value)}
                className="w-full border border-gray-700 rounded-lg px-3 py-2 text-gray-100 bg-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {ACCOUNT_OPTIONS.map((opt) => (
                  <option key={opt.code} value={opt.code}>
                    {opt.code} — {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={startClassification}
              disabled={!file}
              className="w-full py-3 rounded-xl font-medium text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              Classify transactions
            </button>
          </>
        )}

        {/* Progress bar */}
        {running && progress && (
          <div>
            <div className="flex justify-between text-xs text-gray-400 mb-1">
              <span>{question ? '⏸ Waiting for your answer…' : 'Processing…'}</span>
              <span>{progress.index} / {progress.total}</span>
            </div>
            <div className="w-full bg-gray-800 rounded-full h-1.5">
              <div
                className="bg-indigo-500 h-1.5 rounded-full transition-all duration-300"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        )}

        {/* Question card */}
        {question && (
          <div className="border border-amber-500/40 bg-amber-950/30 rounded-xl p-4 space-y-3">
            <div className="flex justify-between items-start">
              <div>
                <p className="font-semibold text-white">{question.transaction.description}</p>
                <p className="text-sm text-gray-400">
                  {question.transaction.date} · {question.transaction.amount.toFixed(2)} €
                </p>
              </div>
              <span className="text-xs bg-amber-500/20 text-amber-300 px-2 py-1 rounded-full border border-amber-500/30">
                AI unsure
              </span>
            </div>
            <p className="text-sm text-gray-400 italic">"{question.reason}"</p>

            {/* Search */}
            <input
              autoFocus
              type="text"
              placeholder="Search category…"
              value={optionSearch}
              onChange={(e) => setOptionSearch(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />

            <div className="grid grid-cols-2 gap-2 max-h-56 overflow-y-auto pr-1">
              {question.options
                .filter((opt) => {
                  const q = optionSearch.toLowerCase()
                  return !q || opt.code.toLowerCase().includes(q) || opt.label.toLowerCase().includes(q)
                })
                .map((opt) => (
                <button
                  key={opt.code}
                  onClick={() => handleAnswer(opt.code)}
                  className={`text-left px-3 py-2 rounded-lg text-sm border transition-colors
                    ${opt.code === question.suggestion
                      ? 'border-indigo-500 bg-indigo-900/50 text-indigo-200 font-medium'
                      : 'border-gray-700 bg-gray-900 text-gray-300 hover:border-indigo-500 hover:bg-gray-800'}`}
                >
                  <span className="font-mono text-xs text-gray-500">{opt.code}</span>
                  <br />
                  {opt.label}
                </button>
              ))}
            </div>

          </div>
        )}
      </div>

      {/* Terminal log panel */}
      <div className="w-full max-w-2xl flex-1">
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          {/* Title bar */}
          <div className="flex items-center gap-1.5 px-4 py-2 border-b border-gray-800 bg-gray-950">
            <span className="w-3 h-3 rounded-full bg-red-500/70" />
            <span className="w-3 h-3 rounded-full bg-yellow-500/70" />
            <span className="w-3 h-3 rounded-full bg-green-500/70" />
            <span className="ml-3 text-xs text-gray-500 font-mono">pnl-ai — classifier</span>
          </div>
          {/* Log output */}
          <div className="h-72 overflow-y-auto p-4 font-mono text-xs leading-5">
            {logs.length === 0 && (
              <span className="text-gray-600">Waiting for classification to start…</span>
            )}
            {logs.map((line, i) => (
              <div
                key={i}
                className={
                  line.type === 'ok' ? 'text-green-400' :
                  line.type === 'warn' ? 'text-yellow-400' :
                  line.type === 'question' ? 'text-amber-300' :
                  'text-gray-400'
                }
              >
                {line.text}
              </div>
            ))}
            <div ref={logEndRef} />
          </div>
        </div>
      </div>
    </div>
  )
}
