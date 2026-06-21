import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import JobCard from './JobCard'

export default function Column({ column, jobs, onEdit, onDelete, onAdd }) {
  const { setNodeRef, isOver } = useDroppable({ id: column.id })

  return (
    <div className="flex-shrink-0 w-72 flex flex-col max-h-[calc(100vh-73px)]">
      {/* Header */}
      <div className="flex items-center justify-between mb-2 px-1 flex-shrink-0">
        <div className="flex items-center gap-2">
          <span
            className="w-2.5 h-2.5 rounded-full flex-shrink-0"
            style={{ backgroundColor: column.color }}
          />
          <h2 className="font-semibold text-sm text-gray-700 dark:text-gray-300">
            {column.label}
          </h2>
          <span className="text-xs font-semibold px-1.5 py-0.5 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400 min-w-[20px] text-center">
            {jobs.length}
          </span>
        </div>
        <button
          onClick={onAdd}
          className="w-6 h-6 flex items-center justify-center rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors text-base font-medium"
          title={`Add job to ${column.label}`}
        >
          +
        </button>
      </div>

      {/* Cards container — scrollable */}
      <SortableContext items={jobs.map(j => j.id)} strategy={verticalListSortingStrategy}>
        <div
          ref={setNodeRef}
          className={`
            flex-1 flex flex-col gap-2 overflow-y-auto scrollbar-thin p-2 rounded-xl transition-colors
            ${isOver
              ? 'bg-blue-50 dark:bg-blue-900/20 ring-2 ring-blue-400 ring-dashed'
              : 'bg-gray-200/60 dark:bg-gray-800/60'
            }
          `}
        >
          {jobs.map(job => (
            <JobCard
              key={job.id}
              job={job}
              columnColor={column.color}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          ))}
          {jobs.length === 0 && (
            <div className="flex-1 flex items-center justify-center py-10 text-xs text-gray-400 dark:text-gray-600 select-none">
              Drop here
            </div>
          )}
        </div>
      </SortableContext>
    </div>
  )
}
