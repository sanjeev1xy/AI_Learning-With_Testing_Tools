import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const CHROMA_DIR = path.join(__dirname, '..', 'chroma_db')

function collectionFile(name) {
  return path.join(CHROMA_DIR, `${name}.json`)
}

function loadCollection(name) {
  const file = collectionFile(name)
  if (!fs.existsSync(file)) return { ids: [], embeddings: [], documents: [], metadatas: [] }
  return JSON.parse(fs.readFileSync(file, 'utf-8'))
}

function saveCollection(name, data) {
  fs.mkdirSync(CHROMA_DIR, { recursive: true })
  fs.writeFileSync(collectionFile(name), JSON.stringify(data))
}

export function resetCollection(name) {
  const file = collectionFile(name)
  if (fs.existsSync(file)) fs.unlinkSync(file)
}

export function addToCollection(name, { ids, embeddings, documents, metadatas }) {
  saveCollection(name, { ids, embeddings, documents, metadatas })
}

export function getCollectionCount(name) {
  return loadCollection(name).ids.length
}

function dotProduct(a, b) {
  let sum = 0
  for (let i = 0; i < a.length; i++) sum += a[i] * b[i]
  return sum
}

export function queryCollection(name, queryEmbedding, topK) {
  const { ids, embeddings, documents, metadatas } = loadCollection(name)

  const scored = ids.map((id, i) => ({
    id,
    document: documents[i],
    metadata: metadatas[i],
    similarity: dotProduct(queryEmbedding, embeddings[i]),
  }))

  scored.sort((a, b) => b.similarity - a.similarity)
  return scored.slice(0, topK)
}
