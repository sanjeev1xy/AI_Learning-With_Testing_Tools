import { useState, useMemo, useEffect } from 'react'
import { useJobs } from './hooks/useJobs'
import Header from './components/Header'
import KanbanBoard from './components/KanbanBoard'
import JobModal from './components/JobModal'

export default function App() {
  const { jobs, loading, add, update, remove, move } = useJobs()

  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark')
  const [search, setSearch] = useState('')
  const [sortOrder, setSortOrder] = useState('newest')
  const [modal, setModal] = useState({ open: false, job: null, defaultStatus: 'wishlist' })

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    localStorage.setItem('theme', theme)
  }, [theme])

  const filteredJobs = useMemo(() => {
    const q = search.toLowerCase()
    if (!q) return jobs
    return jobs.filter(
      j =>
        j.company.toLowerCase().includes(q) ||
        j.role.toLowerCase().includes(q)
    )
  }, [jobs, search])

  const openAdd = (status = 'wishlist') =>
    setModal({ open: true, job: null, defaultStatus: status })

  const openEdit = (job) =>
    setModal({ open: true, job, defaultStatus: job.status })

  const closeModal = () =>
    setModal(m => ({ ...m, open: false }))

  const handleSave = async (data) => {
    if (modal.job) {
      await update({ ...modal.job, ...data })
    } else {
      await add({ status: modal.defaultStatus, ...data })
    }
    closeModal()
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this job? This cannot be undone.')) return
    await remove(id)
  }

  const handleExport = () => {
    const blob = new Blob([JSON.stringify(jobs, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `job-tracker-${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleImport = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    try {
      const text = await file.text()
      const data = JSON.parse(text)
      if (!Array.isArray(data)) throw new Error('Expected a JSON array')
      let imported = 0
      let skipped = 0
      for (const job of data) {
        try {
          await add(job)
          imported++
        } catch {
          skipped++
        }
      }
      alert(`Imported ${imported} jobs.${skipped ? ` Skipped ${skipped} duplicates.` : ''}`)
    } catch (err) {
      alert('Import failed: ' + err.message)
    }
    e.target.value = ''
  }

  const existingResumes = useMemo(
    () => [...new Set(jobs.map(j => j.resumeUsed).filter(Boolean))],
    [jobs]
  )

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <Header
        search={search}
        onSearch={setSearch}
        theme={theme}
        onToggleTheme={() => setTheme(t => (t === 'dark' ? 'light' : 'dark'))}
        onAdd={() => openAdd()}
        onExport={handleExport}
        onImport={handleImport}
        sortOrder={sortOrder}
        onSortChange={setSortOrder}
        totalJobs={jobs.length}
      />

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent" />
        </div>
      ) : (
        <KanbanBoard
          jobs={filteredJobs}
          sortOrder={sortOrder}
          onMove={move}
          onEdit={openEdit}
          onDelete={handleDelete}
          onAddToColumn={openAdd}
        />
      )}

      {modal.open && (
        <JobModal
          job={modal.job}
          defaultStatus={modal.defaultStatus}
          onSave={handleSave}
          onClose={closeModal}
          existingResumes={existingResumes}
        />
      )}
    </div>
  )
}
