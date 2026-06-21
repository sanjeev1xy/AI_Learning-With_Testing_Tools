import { useState, useEffect, useRef } from 'react'
import { COLUMNS } from './KanbanBoard'

const TODAY = new Date().toISOString().split('T')[0]

const EMPTY = {
  company: '',
  role: '',
  linkedinUrl: '',
  resumeUsed: '',
  dateApplied: TODAY,
  salaryRange: '',
  notes: '',
  status: 'wishlist',
}

export default function JobModal({ job, defaultStatus, onSave, onClose, existingResumes }) {
  const [form, setForm] = useState(EMPTY)
  const [errors, setErrors] = useState({})
  const [saving, setSaving] = useState(false)
  const firstInputRef = useRef(null)

  useEffect(() => {
    if (job) {
      setForm({ ...EMPTY, ...job })
    } else {
      setForm({ ...EMPTY, status: defaultStatus || 'wishlist' })
    }
    setErrors({})
    setTimeout(() => firstInputRef.current?.focus(), 50)
  }, [job, defaultStatus])

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const set = (field) => (e) => {
    setForm(prev => ({ ...prev, [field]: e.target.value }))
    if (errors[field]) setErrors(prev => ({ ...prev, [field]: null }))
  }

  const validate = () => {
    const errs = {}
    if (!form.company.trim()) errs.company = 'Required'
    if (!form.role.trim()) errs.role = 'Required'
    if (form.linkedinUrl && !form.linkedinUrl.startsWith('http')) {
      errs.linkedinUrl = 'Must start with http(s)://'
    }
    return errs
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }
    setSaving(true)
    try {
      await onSave(form)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[92vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
          <h2 className="text-base font-bold text-gray-900 dark:text-white">
            {job ? 'Edit Job' : 'Add Job'}
          </h2>
          <button
            onClick={onClose}
            className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-lg"
          >
            ×
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto scrollbar-thin px-6 py-5 flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Company *" error={errors.company}>
              <input
                ref={firstInputRef}
                value={form.company}
                onChange={set('company')}
                className={inputCls(errors.company)}
                placeholder="Google"
              />
            </Field>
            <Field label="Role *" error={errors.role}>
              <input
                value={form.role}
                onChange={set('role')}
                className={inputCls(errors.role)}
                placeholder="Senior SDE"
              />
            </Field>
          </div>

          <Field label="Status">
            <select value={form.status} onChange={set('status')} className={inputCls()}>
              {COLUMNS.map(c => (
                <option key={c.id} value={c.id}>{c.label}</option>
              ))}
            </select>
          </Field>

          <Field label="LinkedIn Job URL" error={errors.linkedinUrl}>
            <input
              type="url"
              value={form.linkedinUrl}
              onChange={set('linkedinUrl')}
              className={inputCls(errors.linkedinUrl)}
              placeholder="https://linkedin.com/jobs/view/..."
            />
          </Field>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Date Applied">
              <input
                type="date"
                value={form.dateApplied}
                onChange={set('dateApplied')}
                className={inputCls()}
              />
            </Field>
            <Field label="Salary Range">
              <input
                value={form.salaryRange}
                onChange={set('salaryRange')}
                className={inputCls()}
                placeholder="₹25–30 LPA"
              />
            </Field>
          </div>

          <Field label="Resume Used">
            <input
              list="resume-list"
              value={form.resumeUsed}
              onChange={set('resumeUsed')}
              className={inputCls()}
              placeholder="SDE_Resume_v3"
            />
            <datalist id="resume-list">
              {existingResumes.map(r => <option key={r} value={r} />)}
            </datalist>
          </Field>

          <Field label="Notes">
            <textarea
              value={form.notes}
              onChange={set('notes')}
              className={`${inputCls()} resize-none h-20`}
              placeholder="Recruiter: Jane Doe · Referral: John Smith"
            />
          </Field>
        </form>

        {/* Footer */}
        <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex-shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="px-5 py-2 text-sm rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold transition-colors shadow-sm disabled:opacity-60"
          >
            {saving ? 'Saving…' : job ? 'Save Changes' : 'Add Job'}
          </button>
        </div>
      </div>
    </div>
  )
}

function Field({ label, error, children }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">
        {label}
      </label>
      {children}
      {error && <span className="text-xs text-red-500">{error}</span>}
    </div>
  )
}

function inputCls(error) {
  return [
    'w-full px-3 py-2 text-sm rounded-lg border transition-colors',
    'bg-white dark:bg-gray-700',
    'focus:outline-none focus:ring-2',
    error
      ? 'border-red-400 focus:ring-red-400'
      : 'border-gray-200 dark:border-gray-600 focus:ring-blue-500',
  ].join(' ')
}
