import { openDB } from 'idb'

const DB_NAME = 'job-tracker'
const STORE = 'jobs'
const VERSION = 1

function getDB() {
  return openDB(DB_NAME, VERSION, {
    upgrade(db) {
      if (!db.objectStoreNames.contains(STORE)) {
        const store = db.createObjectStore(STORE, { keyPath: 'id' })
        store.createIndex('status', 'status')
        store.createIndex('createdAt', 'createdAt')
      }
    },
  })
}

export async function getAllJobs() {
  const db = await getDB()
  return db.getAll(STORE)
}

export async function addJob(job) {
  const db = await getDB()
  await db.add(STORE, job)
}

export async function updateJob(job) {
  const db = await getDB()
  await db.put(STORE, job)
}

export async function deleteJob(id) {
  const db = await getDB()
  await db.delete(STORE, id)
}
