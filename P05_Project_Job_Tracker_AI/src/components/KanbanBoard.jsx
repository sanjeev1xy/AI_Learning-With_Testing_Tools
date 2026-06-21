import { useState } from 'react'
import {
  DndContext,
  DragOverlay,
  closestCorners,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import Column from './Column'
import JobCard from './JobCard'

export const COLUMNS = [
  { id: 'wishlist',  label: 'Wishlist',   color: '#6366f1' },
  { id: 'applied',   label: 'Applied',    color: '#3b82f6' },
  { id: 'followup',  label: 'Follow-up',  color: '#f59e0b' },
  { id: 'interview', label: 'Interview',  color: '#8b5cf6' },
  { id: 'offer',     label: 'Offer',      color: '#10b981' },
  { id: 'rejected',  label: 'Rejected',   color: '#ef4444' },
]

export default function KanbanBoard({ jobs, sortOrder, onMove, onEdit, onDelete, onAddToColumn }) {
  const [activeJob, setActiveJob] = useState(null)

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } })
  )

  const findContainer = (id) => {
    if (COLUMNS.find(c => c.id === id)) return id
    return jobs.find(j => j.id === id)?.status ?? null
  }

  const handleDragStart = ({ active }) => {
    setActiveJob(jobs.find(j => j.id === active.id) ?? null)
  }

  const handleDragEnd = ({ active, over }) => {
    setActiveJob(null)
    if (!over) return
    const fromCol = findContainer(active.id)
    const toCol   = findContainer(over.id)
    if (fromCol && toCol && fromCol !== toCol) {
      onMove(active.id, toCol)
    }
  }

  const jobsForColumn = (colId) => {
    const colJobs = jobs.filter(j => j.status === colId)
    return sortOrder === 'oldest'
      ? [...colJobs].sort((a, b) => a.createdAt - b.createdAt)
      : [...colJobs].sort((a, b) => b.createdAt - a.createdAt)
  }

  const activeColumn = activeJob ? COLUMNS.find(c => c.id === activeJob.status) : null

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="flex gap-3 px-4 py-4 overflow-x-auto">
        {COLUMNS.map(col => (
          <Column
            key={col.id}
            column={col}
            jobs={jobsForColumn(col.id)}
            onEdit={onEdit}
            onDelete={onDelete}
            onAdd={() => onAddToColumn(col.id)}
          />
        ))}
      </div>
      <DragOverlay dropAnimation={{ duration: 150 }}>
        {activeJob ? (
          <JobCard
            job={activeJob}
            columnColor={activeColumn?.color ?? '#6366f1'}
            onEdit={() => {}}
            onDelete={() => {}}
            overlay
          />
        ) : null}
      </DragOverlay>
    </DndContext>
  )
}
