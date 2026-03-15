import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

interface TreeNode {
  code: string
  label: string
  children: TreeNode[]
  isLeaf: boolean
}

function buildTree(plan: Record<string, string>): TreeNode[] {
  const codes = Object.keys(plan)

  function isLeaf(code: string): boolean {
    return !codes.some(
      (k) => k !== code && k.startsWith(code) && k.length > code.length && /\d/.test(k[code.length])
    )
  }

  function getChildren(parentCode: string): TreeNode[] {
    const parentLen = parentCode.length
    return codes
      .filter((k) => {
        if (k === parentCode) return false
        if (!k.startsWith(parentCode)) return false
        // Direct child: one level deeper, no intermediate
        const rest = k.slice(parentLen)
        return rest.length > 0 && /^\d/.test(rest) &&
          !codes.some((other) =>
            other !== k && other !== parentCode &&
            other.startsWith(parentCode) &&
            k.startsWith(other) &&
            other.length > parentLen
          )
      })
      .map((k) => ({
        code: k,
        label: plan[k],
        children: getChildren(k),
        isLeaf: isLeaf(k),
      }))
  }

  // Top-level: 1-digit numeric codes
  return codes
    .filter((k) => k.length === 1 && /\d/.test(k))
    .map((k) => ({
      code: k,
      label: plan[k],
      children: getChildren(k),
      isLeaf: isLeaf(k),
    }))
}

interface NodeRowProps {
  node: TreeNode
  depth: number
  onEdit: (code: string, label: string) => void
  editing: string | null
  draft: string
  setDraft: (v: string) => void
  onSave: (code: string) => void
  onCancel: () => void
  saving: boolean
}

function NodeRow({ node, depth, onEdit, editing, draft, setDraft, onSave, onCancel, saving }: NodeRowProps) {
  const [open, setOpen] = useState(depth === 0)
  const hasChildren = node.children.length > 0

  const indent = depth * 20

  return (
    <div>
      <div
        className={`flex items-center gap-3 py-2 px-4 group
          ${depth === 0 ? 'bg-gray-900 border-b border-gray-800' : 'hover:bg-gray-800/40'}
          ${depth === 1 ? 'border-b border-gray-800/40' : ''}`}
        style={{ paddingLeft: `${16 + indent}px` }}
      >
        {/* Expand toggle */}
        <button
          onClick={() => hasChildren && setOpen((o) => !o)}
          className={`w-4 h-4 flex items-center justify-center text-xs shrink-0
            ${hasChildren ? 'text-gray-500 hover:text-gray-300 cursor-pointer' : 'cursor-default'}`}
        >
          {hasChildren ? (open ? '▾' : '▸') : ''}
        </button>

        {/* Code */}
        <span className={`font-mono shrink-0 ${
          depth === 0 ? 'text-sm font-semibold text-gray-300 w-8' :
          depth === 1 ? 'text-xs text-gray-400 w-8' :
                        'text-xs text-gray-600 w-10'
        }`}>
          {node.code}
        </span>

        {/* Label */}
        {editing === node.code ? (
          <div className="flex items-center gap-2 flex-1">
            <input
              autoFocus
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') onSave(node.code)
                if (e.key === 'Escape') onCancel()
              }}
              className="flex-1 bg-gray-800 border border-indigo-500 rounded px-2 py-0.5 text-sm text-gray-100 focus:outline-none"
            />
            <button
              onClick={() => onSave(node.code)}
              disabled={saving}
              className="text-xs px-3 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-50 shrink-0"
            >
              {saving ? '…' : 'Save'}
            </button>
            <button onClick={onCancel} className="text-xs text-gray-500 hover:text-gray-300 shrink-0">
              Cancel
            </button>
          </div>
        ) : (
          <button
            onClick={() => node.isLeaf && onEdit(node.code, node.label)}
            className={`flex-1 text-left flex items-center gap-2 ${!node.isLeaf ? 'cursor-default' : 'group/label'}`}
          >
            <span className={
              depth === 0 ? 'text-sm font-semibold text-gray-200' :
              depth === 1 ? 'text-sm text-gray-300' :
                            'text-sm text-gray-400'
            }>
              {node.label}
            </span>
            {node.isLeaf && (
              <span className="text-gray-700 group-hover/label:text-indigo-400 text-xs opacity-0 group-hover/label:opacity-100 transition-opacity">✏</span>
            )}
          </button>
        )}
      </div>

      {/* Children */}
      {open && hasChildren && (
        <div>
          {node.children.map((child) => (
            <NodeRow
              key={child.code}
              node={child}
              depth={depth + 1}
              onEdit={onEdit}
              editing={editing}
              draft={draft}
              setDraft={setDraft}
              onSave={onSave}
              onCancel={onCancel}
              saving={saving}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default function Categories() {
  const navigate = useNavigate()
  const [plan, setPlan] = useState<Record<string, string>>({})
  const [editing, setEditing] = useState<string | null>(null)
  const [draft, setDraft] = useState('')
  const [search, setSearch] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetch('/api/categories/plan').then((r) => r.json()).then(setPlan)
  }, [])

  const tree = buildTree(plan)

  const startEdit = (code: string, label: string) => { setEditing(code); setDraft(label) }
  const cancelEdit = () => setEditing(null)

  const save = async (code: string) => {
    if (!draft.trim() || draft === plan[code]) { setEditing(null); return }
    setSaving(true)
    await fetch(`/api/categories/${encodeURIComponent(code)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ label: draft.trim() }),
    })
    setPlan((prev) => ({ ...prev, [code]: draft.trim() }))
    setEditing(null)
    setSaving(false)
  }

  // Flat search results
  const searchResults = search
    ? Object.entries(plan).filter(([code, label]) => {
        const q = search.toLowerCase()
        return code.toLowerCase().includes(q) || label.toLowerCase().includes(q)
      })
    : null

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6">
      <div className="max-w-2xl mx-auto space-y-5">

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-white">Categories</h1>
            <p className="text-gray-500 text-sm">{Object.keys(plan).length} entries · click any leaf to rename</p>
          </div>
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 rounded-lg border border-gray-700 text-gray-400 text-sm hover:border-gray-500 transition-colors"
          >
            ← Back
          </button>
        </div>

        <input
          type="text"
          placeholder="Search by code or label…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />

        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          {searchResults ? (
            // Flat search view
            searchResults.map(([code, label]) => (
              <div key={code} className="flex items-center gap-3 px-5 py-2.5 border-b border-gray-800/60 hover:bg-gray-800/40">
                <span className="font-mono text-xs text-gray-500 w-12 shrink-0">{code}</span>
                {editing === code ? (
                  <div className="flex items-center gap-2 flex-1">
                    <input
                      autoFocus
                      value={draft}
                      onChange={(e) => setDraft(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') save(code); if (e.key === 'Escape') cancelEdit() }}
                      className="flex-1 bg-gray-800 border border-indigo-500 rounded px-2 py-0.5 text-sm text-gray-100 focus:outline-none"
                    />
                    <button onClick={() => save(code)} disabled={saving} className="text-xs px-3 py-1 rounded bg-indigo-600 text-white disabled:opacity-50">{saving ? '…' : 'Save'}</button>
                    <button onClick={cancelEdit} className="text-xs text-gray-500 hover:text-gray-300">Cancel</button>
                  </div>
                ) : (
                  <button onClick={() => startEdit(code, label)} className="flex-1 text-left flex items-center gap-2 group/label">
                    <span className="text-sm text-gray-300">{label}</span>
                    <span className="text-gray-700 group-hover/label:text-indigo-400 text-xs opacity-0 group-hover/label:opacity-100 transition-opacity">✏</span>
                  </button>
                )}
              </div>
            ))
          ) : (
            // Tree view
            tree.map((node) => (
              <NodeRow
                key={node.code}
                node={node}
                depth={0}
                onEdit={startEdit}
                editing={editing}
                draft={draft}
                setDraft={setDraft}
                onSave={save}
                onCancel={cancelEdit}
                saving={saving}
              />
            ))
          )}
        </div>

        <p className="text-xs text-gray-600 text-center">
          Edits write to <code className="text-gray-500">categories.py</code>. Restart the backend to apply to the classifier.
        </p>
      </div>
    </div>
  )
}
