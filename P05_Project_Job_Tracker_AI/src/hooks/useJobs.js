import { useState, useEffect, useCallback } from 'react'
import { getAllJobs, addJob, updateJob, deleteJob } from '../db/jobsDb'

export function useJobs() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getAllJobs().then(data => {
      setJobs(data.sort((a, b) => b.createdAt - a.createdAt))
      setLoading(false)
    })
  }, [])

  const add = useCallback(async (jobData) => {
    const job = {
      id: crypto.randomUUID(),
      createdAt: Date.now(),
      ...jobData,
    }
    await addJob(job)
    setJobs(prev => [job, ...prev])
    return job
  }, [])

  const update = useCallback(async (job) => {
    await updateJob(job)
    setJobs(prev => prev.map(j => (j.id === job.id ? job : j)))
  }, [])

  const remove = useCallback(async (id) => {
    await deleteJob(id)
    setJobs(prev => prev.filter(j => j.id !== id))
  }, [])

  const move = useCallback((id, newStatus) => {
    setJobs(prev => {
      const job = prev.find(j => j.id === id)
      if (!job || job.status === newStatus) return prev
      const updated = { ...job, status: newStatus }
      updateJob(updated)
      return prev.map(j => (j.id === id ? updated : j))
    })
  }, [])

  return { jobs, loading, add, update, remove, move }
}
