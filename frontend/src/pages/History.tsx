import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

interface HistoryEntry {
  key: string
  description: string
  category: string
  source_account?: string
}

interface CategoryOption {
  code: string
  label: string
}

export default function History() {
  const navigate = useNavigate()
  const [entries, setEntries] = useState<HistoryEntry[]>([])
  const [categories, setCategories] = useState<CategoryOption[]>([])
  const [search, setSearch] = useState('')
  const [editing, setEditing] = useState<string | null>(null)
  const [editSearch, setEditSearch] = useState('')

  useEffect(() => {
    fetch('/api/history').then((r) => r.json()).then(setEntries)
    fetch('/api/categories').then((r) => r.json()).then(setCategories)
  }, [])

  const filtered = entries.filter((e) => {
    const q = search.toLowerCase()
    return !q || e.description.toLowerCase().includes(q) || e.category.toLowerCase().includes(q)
  })

  const filteredCats = categories.filter((c) => {
    const q = editSearch.toLowerCase()
    return !q || c.code.toLowerCase().includes(q) || c.label.toLowerCase().includes(q)
  })

  const updateCategory = async (entry: HistoryEntry, newCategory: string) => {
    await fetch(`/api/history/${encodeURIComponent(entry.key)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category: newCategory }),
    })
    setEntries((prev) =>
      prev.map((e) => e.key === entry.key ? { ...e, category: newCategory } : e)
    )
    setEditing(null)
    setEditSearch('')
  }

  const deleteEntry = async (key: string) => {
    await fetch(`/api/history/${encodeURIComponent(key)}`, { method: 'DELETE' })
    setEntries((prev) => prev.filter((e) => e.key !== key))
  }

  const categoryLabel = (code: string) =>
    categories.find((c) => c.code === code)?.label ?? code

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6">
      <div className="max-w-4xl mx-auto space-y-5">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-white">History</h1>
            <p className="text-gray-400 text-sm">{entries.length} learned classifications</p>
          </div>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 rounded-lg border border-gray-700 text-gray-400 text-sm hover:border-gray-500 transition-colors"
          >
            ← Back
          </button>
        </div>

        {/* Search */}
        <input
          autoFocus
          type="text"
          placeholder="Search by description or category…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />

        {/* Table */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-950 text-gray-500 text-xs uppercase tracking-wide">
              <tr>
                <th className="px-5 py-3 text-left">Description</th>
                <th className="px-5 py-3 text-left">Category</th>
                <th className="px-5 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {filtered.map((entry) => (
                <tr key={entry.key} className="hover:bg-gray-800/50">
                  <td className="px-5 py-3 text-gray-300">{entry.description}</td>
                  <td className="px-5 py-3">
                    {editing === entry.key ? (
                      <div className="space-y-1.5">
                        <input
                          autoFocus
                          type="text"
                          placeholder="Search…"
                          value={editSearch}
                          onChange={(e) => setEditSearch(e.target.value)}
                          className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1 text-xs text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        />
                        <div className="max-h-40 overflow-y-auto space-y-0.5">
                          {filteredCats.map((cat) => (
                            <button
                              key={cat.code}
                              onClick={() => updateCategory(entry, cat.code)}
                              className={`w-full text-left px-2 py-1 rounded text-xs transition-colors
                                ${cat.code === entry.category
                                  ? 'bg-indigo-900/60 text-indigo-300'
                                  : 'text-gray-300 hover:bg-gray-700'}`}
                            >
                              <span className="font-mono text-gray-500 mr-1.5">{cat.code}</span>
                              {cat.label}
                            </button>
                          ))}
                        </div>
                        <button
                          onClick={() => { setEditing(null); setEditSearch('') }}
                          className="text-xs text-gray-500 hover:text-gray-300"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => { setEditing(entry.key); setEditSearch('') }}
                        className="flex items-center gap-2 group"
                      >
                        <span className="font-mono text-xs text-gray-500">{entry.category}</span>
                        <span className="text-gray-300">{categoryLabel(entry.category)}</span>
                        <span className="text-gray-600 group-hover:text-indigo-400 text-xs">✏</span>
                      </button>
                    )}
                  </td>
                  <td className="px-5 py-3 text-right">
                    <button
                      onClick={() => deleteEntry(entry.key)}
                      className="text-gray-600 hover:text-red-400 text-xs transition-colors"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}

              {filtered.length === 0 && (
                <tr>
                  <td colSpan={3} className="px-5 py-8 text-center text-gray-600">
                    {search ? 'No matches found.' : 'No history yet.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
