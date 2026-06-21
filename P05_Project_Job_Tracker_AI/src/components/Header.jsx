export default function Header({
  search,
  onSearch,
  theme,
  onToggleTheme,
  onAdd,
  onExport,
  onImport,
  sortOrder,
  onSortChange,
  totalJobs,
}) {
  return (
    <header className="sticky top-0 z-40 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
      <div className="max-w-screen-2xl mx-auto px-4 py-3 flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2 mr-1 flex-shrink-0">
          <span className="text-xl">💼</span>
          <h1 className="text-lg font-bold text-gray-900 dark:text-white tracking-tight">
            Job Tracker
          </h1>
          <span className="text-xs font-medium px-1.5 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300">
            {totalJobs}
          </span>
        </div>

        <div className="flex-1 min-w-[180px]">
          <input
            type="text"
            placeholder="Search company or role..."
            value={search}
            onChange={e => onSearch(e.target.value)}
            className="w-full px-3 py-1.5 text-sm rounded-lg bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400"
          />
        </div>

        <select
          value={sortOrder}
          onChange={e => onSortChange(e.target.value)}
          className="text-sm px-2 py-1.5 rounded-lg bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
        >
          <option value="newest">Newest first</option>
          <option value="oldest">Oldest first</option>
        </select>

        <div className="flex items-center gap-2 flex-shrink-0">
          <label className="cursor-pointer text-sm px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 border border-gray-200 dark:border-gray-600 transition-colors select-none">
            Import
            <input type="file" accept=".json" className="hidden" onChange={onImport} />
          </label>
          <button
            onClick={onExport}
            className="text-sm px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 border border-gray-200 dark:border-gray-600 transition-colors"
          >
            Export
          </button>
          <button
            onClick={onToggleTheme}
            className="text-sm px-2.5 py-1.5 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 border border-gray-200 dark:border-gray-600 transition-colors"
            title="Toggle theme"
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
          <button
            onClick={onAdd}
            className="text-sm px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold transition-colors shadow-sm"
          >
            + Add Job
          </button>
        </div>
      </div>
    </header>
  )
}
