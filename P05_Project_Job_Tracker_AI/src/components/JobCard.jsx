import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

function daysSince(dateStr) {
  if (!dateStr) return null
  const d = new Date(dateStr)
  const now = new Date()
  return Math.floor((now - d) / (1000 * 60 * 60 * 24))
}

function LinkedInIcon() {
  return (
    <svg viewBox="0 0 24 24" className="w-3.5 h-3.5 fill-current">
      <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" />
    </svg>
  )
}

export default function JobCard({ job, columnColor, onEdit, onDelete, overlay }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: job.id,
    disabled: !!overlay,
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    borderLeftColor: columnColor,
  }

  const days = daysSince(job.dateApplied)

  if (overlay) {
    return (
      <div
        className="bg-white dark:bg-gray-800 rounded-lg p-3 shadow-2xl border-l-4 rotate-1 opacity-95 w-72"
        style={{ borderLeftColor: columnColor }}
      >
        <p className="font-semibold text-sm text-gray-900 dark:text-gray-100">{job.company}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{job.role}</p>
      </div>
    )
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={`
        group relative bg-white dark:bg-gray-800 rounded-lg p-3
        border-l-4 shadow-sm hover:shadow-md transition-shadow
        cursor-grab active:cursor-grabbing select-none
        ${isDragging ? 'opacity-30' : 'opacity-100'}
      `}
    >
      {/* Action buttons — appear on hover */}
      <div className="absolute top-2 right-2 flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onPointerDown={e => e.stopPropagation()}
          onClick={e => { e.stopPropagation(); onEdit(job) }}
          className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
          title="Edit"
        >
          <svg viewBox="0 0 20 20" className="w-3.5 h-3.5 fill-current">
            <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
          </svg>
        </button>
        <button
          onPointerDown={e => e.stopPropagation()}
          onClick={e => { e.stopPropagation(); onDelete(job.id) }}
          className="p-1 rounded hover:bg-red-50 dark:hover:bg-red-900/20 text-gray-400 hover:text-red-500 transition-colors"
          title="Delete"
        >
          <svg viewBox="0 0 20 20" className="w-3.5 h-3.5 fill-current">
            <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        </button>
      </div>

      {/* Company & Role */}
      <div className="pr-14">
        <p className="font-semibold text-sm text-gray-900 dark:text-gray-100 leading-tight">
          {job.company}
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 leading-tight">
          {job.role}
        </p>
      </div>

      {/* Tags */}
      {(job.resumeUsed || job.salaryRange) && (
        <div className="flex items-center gap-2 mt-2 flex-wrap">
          {job.resumeUsed && (
            <span className="text-xs px-1.5 py-0.5 rounded font-mono bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 max-w-[140px] truncate">
              {job.resumeUsed}
            </span>
          )}
          {job.salaryRange && (
            <span className="text-xs text-emerald-700 dark:text-emerald-400 font-medium">
              {job.salaryRange}
            </span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-100 dark:border-gray-700">
        <span className="text-xs text-gray-400 dark:text-gray-500">
          {days === null ? '—' : days === 0 ? 'Today' : `${days}d ago`}
        </span>
        <div className="flex items-center gap-2">
          {job.notes && (
            <span className="text-xs text-gray-400 dark:text-gray-500" title={job.notes}>
              📝
            </span>
          )}
          {job.linkedinUrl && (
            <a
              href={job.linkedinUrl}
              target="_blank"
              rel="noopener noreferrer"
              onPointerDown={e => e.stopPropagation()}
              onClick={e => e.stopPropagation()}
              className="text-blue-500 hover:text-blue-600 transition-colors"
              title="View LinkedIn posting"
            >
              <LinkedInIcon />
            </a>
          )}
        </div>
      </div>
    </div>
  )
}
