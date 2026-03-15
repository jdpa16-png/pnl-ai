export interface Transaction {
  date: string
  description: string
  amount: number
  category: string
  category_label?: string
  confidence: 'high' | 'medium' | 'low'
  method: 'hist' | 'kw' | 'ai'
}

export interface ClassifyQuestion {
  type: 'question'
  index: number
  total: number
  transaction: { date: string; description: string; amount: number }
  suggestion: string
  reason: string
  options: { code: string; label: string }[]
}

export interface ClassifyProgress {
  type: 'progress'
  index: number
  total: number
  transaction: Transaction
}

export interface ClassifyDone {
  type: 'done'
  results: Transaction[]
  duplicates: Transaction[]
}

export type WsMessage = ClassifyQuestion | ClassifyProgress | ClassifyDone

export interface AccountOption {
  code: string
  label: string
}

export interface MonthlySummary {
  category: string
  label: string
  total: number
}
