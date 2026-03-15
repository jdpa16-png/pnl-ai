import { useNavigate } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import type { Transaction } from '../types'
import { SHEETS_URL } from '../accounts'
import { useEffect, useMemo, useRef, useState } from 'react'

interface CategoryOption { code: string; label: string }

const CATEGORY_GROUPS: Record<string, { label: string; color: string }> = {
  '4': { label: 'Casa', color: '#6366f1' },
  '5': { label: 'Comer fuera', color: '#f59e0b' },
  '6': { label: 'Compras', color: '#10b981' },
  '7': { label: 'Transporte', color: '#3b82f6' },
  '8': { label: 'Salud & Ocio', color: '#ec4899' },
  '9': { label: 'Financiero', color: '#8b5cf6' },
  'income': { label: 'Ingresos', color: '#22c55e' },
}

function getGroup(code: string): string {
  if (!code || !code[0].match(/\d/)) return 'income'
  return code[0]
}

function formatEur(n: number) {
  return n.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploaded, setUploaded] = useState(false)
  const [editingIdx, setEditingIdx] = useState<number | null>(null)
  const [editSearch, setEditSearch] = useState('')
  const [categories, setCategories] = useState<CategoryOption[]>([])
  const [localResults, setLocalResults] = useState<Transaction[]>([])
  const editRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetch('/api/categories').then((r) => r.json()).then(setCategories)
  }, [])

  useEffect(() => {
    fetch('/api/staging')
      .then((r) => (r.ok ? r.json() : []))
      .then((rows) => setLocalResults(Array.isArray(rows) ? rows : []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  // Close edit dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (editRef.current && !editRef.current.contains(e.target as Node)) {
        setEditingIdx(null)
        setEditSearch('')
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const updateCategory = (idx: number, newCategory: string) => {
    setLocalResults((prev) =>
      prev.map((r, i) => i === idx ? { ...r, category: newCategory } : r)
    )
    setEditingIdx(null)
    setEditSearch('')
  }

  const categoryLabel = (code: string) =>
    categories.find((c) => c.code === code)?.label ?? code

  const filteredCats = categories.filter((c) => {
    const q = editSearch.toLowerCase()
    return !q || c.code.toLowerCase().includes(q) || c.label.toLowerCase().includes(q)
  })

  const expenses = localResults.filter((r) => r.amount < 0)
  const income = localResults.filter((r) => r.amount > 0)
  const totalExpenses = expenses.reduce((s, r) => s + Math.abs(r.amount), 0)
  const totalIncome = income.reduce((s, r) => s + r.amount, 0)

  // Group by category for chart
  const byCategory = useMemo(() => {
    const map: Record<string, number> = {}
    for (const r of expenses) {
      map[r.category] = (map[r.category] ?? 0) + Math.abs(r.amount)
    }
    return Object.entries(map)
      .map(([code, total]) => ({ code, total }))
      .sort((a, b) => b.total - a.total)
  }, [localResults])

  // Group by group for bar chart
  const byGroup = useMemo(() => {
    const map: Record<string, number> = {}
    for (const r of expenses) {
      const g = getGroup(r.category)
      map[g] = (map[g] ?? 0) + Math.abs(r.amount)
    }
    return Object.entries(map)
      .map(([g, total]) => ({ group: g, label: CATEGORY_GROUPS[g]?.label ?? g, total, color: CATEGORY_GROUPS[g]?.color ?? '#94a3b8' }))
      .sort((a, b) => b.total - a.total)
  }, [localResults])

  const [stagingCleared, setStagingCleared] = useState(false)

  const uploadToSheets = async () => {
    setUploading(true)
    try {
      // Send all staged results; per-entry account_code is stored in each row
      const res = await fetch('/api/upload-sheets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ results: localResults }),
      })
      const data = await res.json()
      setUploaded(true)
      if (data.staging_cleared) setStagingCleared(true)
    } finally {
      setUploading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-gray-400 text-sm">Loading staged transactions…</p>
      </div>
    )
  }

  if (!loading && localResults.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-3">
          <p className="text-gray-500">No staged transactions yet.</p>
          <button onClick={() => navigate('/')} className="text-indigo-600 underline text-sm">
            Upload a file
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto space-y-6">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
            <p className="text-gray-500 text-sm">{localResults.length} staged transactions (pending upload)</p>
          </div>
          <div className="flex gap-3">
            <a
              href={SHEETS_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 bg-white text-gray-700 text-sm hover:border-indigo-400 transition-colors"
            >
              📊 Open Sheets
            </a>
            <div className="flex flex-col items-end gap-1">
              <button
                onClick={uploadToSheets}
                disabled={uploading || uploaded}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm hover:bg-indigo-700 disabled:opacity-50 transition-colors"
              >
                {uploaded ? '✓ Uploaded' : uploading ? 'Uploading…' : '⬆ Upload to Sheets'}
              </button>
              {stagingCleared && (
                <span className="text-xs text-green-500">Staging cleared</span>
              )}
            </div>
            <button
              onClick={() => navigate('/history')}
              className="px-4 py-2 rounded-lg border border-gray-700 bg-gray-900 text-gray-300 text-sm hover:border-gray-500 transition-colors"
            >
              📚 History
            </button>
            <button
              onClick={() => navigate('/categories')}
              className="px-4 py-2 rounded-lg border border-gray-700 bg-gray-900 text-gray-300 text-sm hover:border-gray-500 transition-colors"
            >
              🗂 Categories
            </button>
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 rounded-lg border border-gray-300 bg-white text-gray-700 text-sm hover:border-gray-400 transition-colors"
            >
              ← New file
            </button>
          </div>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: 'Total expenses', value: formatEur(totalExpenses), color: 'text-red-600' },
            { label: 'Total income', value: formatEur(totalIncome), color: 'text-green-600' },
            { label: 'Balance', value: formatEur(totalIncome - totalExpenses), color: totalIncome - totalExpenses >= 0 ? 'text-green-600' : 'text-red-600' },
          ].map((c) => (
            <div key={c.label} className="bg-white rounded-xl border border-gray-200 p-5">
              <p className="text-sm text-gray-500">{c.label}</p>
              <p className={`text-2xl font-semibold mt-1 ${c.color}`}>{c.value}</p>
            </div>
          ))}
        </div>

        {/* Bar chart */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-base font-medium text-gray-700 mb-4">Expenses by group</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={byGroup} margin={{ top: 0, right: 0, left: 10, bottom: 0 }}>
              <XAxis dataKey="label" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `${v}€`} />
              <Tooltip formatter={(v) => formatEur(Number(v))} />
              <Bar dataKey="total" radius={[4, 4, 0, 0]}>
                {byGroup.map((entry) => (
                  <Cell key={entry.group} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Category breakdown table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100">
            <h2 className="text-base font-medium text-gray-700">Category breakdown</h2>
          </div>
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wide">
              <tr>
                <th className="px-5 py-3 text-left">Code</th>
                <th className="px-5 py-3 text-left">Transactions</th>
                <th className="px-5 py-3 text-right">Total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {byCategory.map((row) => (
                <tr key={row.code} className="hover:bg-gray-50">
                  <td className="px-5 py-3 font-mono text-gray-500">{row.code}</td>
                  <td className="px-5 py-3 text-gray-700">
                    {expenses.filter((r) => r.category === row.code).map((r) => r.description).slice(0, 2).join(', ')}
                    {expenses.filter((r) => r.category === row.code).length > 2 && '…'}
                  </td>
                  <td className="px-5 py-3 text-right font-medium text-gray-900">
                    {formatEur(row.total)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Transaction list */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100">
            <h2 className="text-base font-medium text-gray-700">All transactions</h2>
          </div>
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wide">
              <tr>
                <th className="px-5 py-3 text-left">Date</th>
                <th className="px-5 py-3 text-left">Description</th>
                <th className="px-5 py-3 text-left">Category</th>
                <th className="px-5 py-3 text-right">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {localResults.map((r, i) => (
                <tr key={i} className="hover:bg-gray-800/40">
                  <td className="px-5 py-3 text-gray-500 whitespace-nowrap text-xs">{r.date}</td>
                  <td className="px-5 py-3 text-gray-300">{r.description}</td>
                  <td className="px-5 py-3 relative">
                    {editingIdx === i ? (
                      <div ref={editRef} className="absolute z-10 top-1 left-0 w-64 bg-gray-900 border border-gray-700 rounded-xl shadow-xl p-2 space-y-1.5">
                        <input
                          autoFocus
                          type="text"
                          placeholder="Search…"
                          value={editSearch}
                          onChange={(e) => setEditSearch(e.target.value)}
                          className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        />
                        <div className="max-h-44 overflow-y-auto space-y-0.5">
                          {filteredCats.map((cat) => (
                            <button
                              key={cat.code}
                              onClick={() => updateCategory(i, cat.code)}
                              className={`w-full text-left px-2 py-1 rounded text-xs transition-colors
                                ${cat.code === r.category
                                  ? 'bg-indigo-900/60 text-indigo-300'
                                  : 'text-gray-300 hover:bg-gray-700'}`}
                            >
                              <span className="font-mono text-gray-500 mr-1.5">{cat.code}</span>
                              {cat.label}
                            </button>
                          ))}
                        </div>
                      </div>
                    ) : null}
                    <button
                      onClick={() => { setEditingIdx(i); setEditSearch('') }}
                      className="flex items-center gap-1.5 group"
                    >
                      <span className="font-mono text-xs text-gray-600">{r.category}</span>
                      <span className="text-gray-400 text-xs">{categoryLabel(r.category)}</span>
                      <span className="text-gray-700 group-hover:text-indigo-400 text-xs">✏</span>
                    </button>
                  </td>
                  <td className={`px-5 py-3 text-right font-medium ${r.amount < 0 ? 'text-red-400' : 'text-green-400'}`}>
                    {formatEur(r.amount)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
