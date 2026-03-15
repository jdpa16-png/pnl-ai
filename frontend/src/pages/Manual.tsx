import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ACCOUNT_OPTIONS } from '../accounts'

interface CategoryOption { code: string; label: string }

interface Movement {
  id: number
  date: string
  description: string
  amount: string        // string while editing, parsed on upload
  account_code: string  // asset account (FROM for expenses, TO for income)
  category: string      // cost/income code
}

let _id = 0

const today = () => new Date().toISOString().slice(0, 10)

export default function Manual() {
  const navigate = useNavigate()
  const [categories, setCategories] = useState<CategoryOption[]>([])
  const [movements, setMovements] = useState<Movement[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploaded, setUploaded] = useState(false)
  const [catSearch, setCatSearch] = useState('')
  const [catOpen, setCatOpen] = useState(false)

  // Form state
  const [form, setForm] = useState<Omit<Movement, 'id'>>({
    date: today(),
    description: '',
    amount: '',
    account_code: '211',
    category: '',
  })
  const [selectedCatLabel, setSelectedCatLabel] = useState('')

  useEffect(() => {
    fetch('/api/categories').then((r) => r.json()).then(setCategories)
  }, [])

  const filteredCats = categories.filter((c) => {
    const q = catSearch.toLowerCase()
    return !q || c.code.toLowerCase().includes(q) || c.label.toLowerCase().includes(q)
  })

  const selectCategory = (code: string, label: string) => {
    setForm((f) => ({ ...f, category: code }))
    setSelectedCatLabel(label)
    setCatOpen(false)
    setCatSearch('')
  }

  const addMovement = () => {
    if (!form.description.trim() || !form.amount || !form.category || !form.date) return
    setMovements((prev) => [...prev, { ...form, id: ++_id }])
    setForm({ date: today(), description: '', amount: '', account_code: form.account_code, category: form.category })
    setSelectedCatLabel(selectedCatLabel)
    setUploaded(false)
  }

  const removeMovement = (id: number) => {
    setMovements((prev) => prev.filter((m) => m.id !== id))
  }

  const uploadToSheets = async () => {
    if (!movements.length) return
    setUploading(true)
    const results = movements.map((m) => ({
      date: m.date,
      description: m.description,
      amount: parseFloat(m.amount),
      category: m.category,
      account_code: m.account_code,
    }))
    await fetch('/api/upload-sheets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ results }),
    })
    setUploaded(true)
    setUploading(false)
  }

  const amountNum = parseFloat(form.amount)
  const isExpense = !isNaN(amountNum) && amountNum < 0
  const isIncome  = !isNaN(amountNum) && amountNum > 0

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6">
      <div className="max-w-2xl mx-auto space-y-6">

        {/* Header */}
        <div className="flex items-center justify-between pt-2">
          <div>
            <h1 className="text-2xl font-semibold text-white">Manual entry</h1>
            <p className="text-gray-500 text-sm">Add movements by hand and upload to Sheets</p>
          </div>
          <button onClick={() => navigate('/')} className="px-4 py-2 rounded-lg border border-gray-700 text-gray-400 text-sm hover:border-gray-500 transition-colors">
            ← Back
          </button>
        </div>

        {/* Entry form */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
          <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wide">New movement</h2>

          <div className="grid grid-cols-2 gap-3">
            {/* Date */}
            <div>
              <label className="block text-xs text-gray-500 mb-1">Date</label>
              <input
                type="date"
                value={form.date}
                onChange={(e) => setForm((f) => ({ ...f, date: e.target.value }))}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            {/* Amount */}
            <div>
              <label className="block text-xs text-gray-500 mb-1">
                Amount&nbsp;
                <span className={`text-xs font-medium ${isExpense ? 'text-red-400' : isIncome ? 'text-green-400' : 'text-gray-600'}`}>
                  {isExpense ? '— expense' : isIncome ? '+ income' : '(negative = expense)'}
                </span>
              </label>
              <input
                type="number"
                step="0.01"
                placeholder="-12.50"
                value={form.amount}
                onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs text-gray-500 mb-1">Description</label>
            <input
              type="text"
              placeholder="e.g. Dinner at La Latina"
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            {/* Asset account */}
            <div>
              <label className="block text-xs text-gray-500 mb-1">Asset account</label>
              <select
                value={form.account_code}
                onChange={(e) => setForm((f) => ({ ...f, account_code: e.target.value }))}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {ACCOUNT_OPTIONS.map((opt) => (
                  <option key={opt.code} value={opt.code}>{opt.code} — {opt.label}</option>
                ))}
              </select>
            </div>

            {/* Category — searchable dropdown */}
            <div className="relative">
              <label className="block text-xs text-gray-500 mb-1">Category (cost / income)</label>
              <button
                type="button"
                onClick={() => { setCatOpen((o) => !o); setCatSearch('') }}
                className={`w-full bg-gray-800 border rounded-lg px-3 py-2 text-sm text-left transition-colors focus:outline-none
                  ${form.category ? 'text-gray-100' : 'text-gray-500'}
                  ${catOpen ? 'border-indigo-500' : 'border-gray-700 hover:border-gray-500'}`}
              >
                {form.category ? (
                  <><span className="font-mono text-gray-500 text-xs">{form.category}</span> {selectedCatLabel}</>
                ) : 'Select…'}
              </button>

              {catOpen && (
                <div className="absolute z-20 top-full mt-1 left-0 right-0 bg-gray-900 border border-gray-700 rounded-xl shadow-xl overflow-hidden">
                  <div className="p-2 border-b border-gray-800">
                    <input
                      autoFocus
                      type="text"
                      placeholder="Search…"
                      value={catSearch}
                      onChange={(e) => setCatSearch(e.target.value)}
                      className="w-full bg-gray-800 rounded px-2 py-1 text-xs text-gray-100 placeholder-gray-600 focus:outline-none"
                    />
                  </div>
                  <div className="max-h-48 overflow-y-auto">
                    {filteredCats.map((cat) => (
                      <button
                        key={cat.code}
                        onClick={() => selectCategory(cat.code, cat.label)}
                        className={`w-full text-left px-3 py-2 text-xs transition-colors
                          ${cat.code === form.category
                            ? 'bg-indigo-900/60 text-indigo-300'
                            : 'text-gray-300 hover:bg-gray-800'}`}
                      >
                        <span className="font-mono text-gray-500 mr-2">{cat.code}</span>
                        {cat.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Double-entry preview */}
          {form.description && form.amount && form.category && !isNaN(amountNum) && amountNum !== 0 && (
            <div className="bg-gray-800/50 rounded-lg p-3 font-mono text-xs space-y-1 text-gray-400">
              <p className="text-gray-500 text-xs mb-1">Preview (double-entry):</p>
              {amountNum < 0 ? <>
                <p><span className="text-gray-600">{form.account_code}</span> · {ACCOUNT_OPTIONS.find(a => a.code === form.account_code)?.label} · <span className="text-red-400">{amountNum.toFixed(2)} €</span></p>
                <p><span className="text-gray-600">{form.category}</span> · {selectedCatLabel} · <span className="text-green-400">{Math.abs(amountNum).toFixed(2)} €</span></p>
              </> : <>
                <p><span className="text-gray-600">{form.category}</span> · {selectedCatLabel} · <span className="text-red-400">{(-amountNum).toFixed(2)} €</span></p>
                <p><span className="text-gray-600">{form.account_code}</span> · {ACCOUNT_OPTIONS.find(a => a.code === form.account_code)?.label} · <span className="text-green-400">{amountNum.toFixed(2)} €</span></p>
              </>}
            </div>
          )}

          <button
            onClick={addMovement}
            disabled={!form.description.trim() || !form.amount || !form.category || !form.date}
            className="w-full py-2.5 rounded-xl font-medium text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            + Add to list
          </button>
        </div>

        {/* Pending movements list */}
        {movements.length > 0 && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            <div className="flex items-center justify-between px-5 py-3 border-b border-gray-800">
              <h2 className="text-sm font-medium text-gray-300">{movements.length} movement{movements.length !== 1 ? 's' : ''} pending</h2>
              <button
                onClick={uploadToSheets}
                disabled={uploading || uploaded}
                className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-indigo-600 text-white text-sm hover:bg-indigo-500 disabled:opacity-50 transition-colors"
              >
                {uploaded ? '✓ Uploaded to Sheets' : uploading ? 'Uploading…' : '⬆ Upload to Sheets'}
              </button>
            </div>
            <table className="w-full text-xs">
              <thead className="bg-gray-950 text-gray-500 uppercase tracking-wide">
                <tr>
                  <th className="px-5 py-2 text-left">Date</th>
                  <th className="px-5 py-2 text-left">Description</th>
                  <th className="px-5 py-2 text-left">Account → Category</th>
                  <th className="px-5 py-2 text-right">Amount</th>
                  <th className="px-4 py-2"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {movements.map((m) => {
                  const amt = parseFloat(m.amount)
                  return (
                    <tr key={m.id} className="hover:bg-gray-800/40">
                      <td className="px-5 py-2.5 text-gray-500 whitespace-nowrap">{m.date}</td>
                      <td className="px-5 py-2.5 text-gray-300">{m.description}</td>
                      <td className="px-5 py-2.5 text-gray-500 font-mono">
                        {m.account_code} → {m.category}
                      </td>
                      <td className={`px-5 py-2.5 text-right font-medium ${amt < 0 ? 'text-red-400' : 'text-green-400'}`}>
                        {amt.toFixed(2)} €
                      </td>
                      <td className="px-4 py-2.5">
                        <button onClick={() => removeMovement(m.id)} className="text-gray-600 hover:text-red-400 transition-colors">✕</button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
