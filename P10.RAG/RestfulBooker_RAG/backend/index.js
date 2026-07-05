import cors from 'cors'
import dotenv from 'dotenv'
import express from 'express'
import fs from 'fs'
import multer from 'multer'
import path from 'path'
import { fileURLToPath } from 'url'

import { findSourceDocument, readDocument, SUPPORTED_EXTENSIONS } from './lib/pdf.js'
import { chunkText, CHUNK_SIZE, CHUNK_OVERLAP } from './lib/chunk.js'
import { embedDocuments, embedQuery, MODEL_NAME } from './lib/embed.js'
import { resetCollection, addToCollection, getCollectionCount, queryCollection } from './lib/chroma.js'
import { generateAnswer, buildAugmentedPrompt, GROQ_MODEL } from './lib/groq.js'

dotenv.config()

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const DATA_DIR = path.join(__dirname, '..', 'data')
const COLLECTION_NAME = 'test_plan_docs'
const TOP_K = 4

fs.mkdirSync(DATA_DIR, { recursive: true })

const app = express()
app.use(cors({ origin: ['http://localhost:5173', 'http://127.0.0.1:5173'] }))
app.use(express.json())

const upload = multer({ storage: multer.memoryStorage() })

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' })
})

app.get('/api/status', (req, res) => {
  const count = getCollectionCount(COLLECTION_NAME)
  res.json({ ingested: count > 0, num_chunks: count })
})

app.post('/api/upload', upload.single('file'), (req, res) => {
  if (!req.file) return res.status(400).json({ detail: 'No file provided' })

  const safeName = path.basename(req.file.originalname)
  const ext = path.extname(safeName).toLowerCase()
  if (!SUPPORTED_EXTENSIONS.has(ext)) {
    return res.status(400).json({ detail: 'Only .pdf and .txt files are supported' })
  }

  const dest = path.join(DATA_DIR, safeName)
  fs.writeFileSync(dest, req.file.buffer)
  res.json({ filename: safeName, size: req.file.buffer.length })
})

app.post('/api/ingest', async (req, res) => {
  try {
    const sourcePath = findSourceDocument(DATA_DIR)
    const { text: fullText, numPages } = await readDocument(sourcePath)
    if (!fullText.trim()) {
      return res.status(500).json({ detail: `No extractable text found in ${path.basename(sourcePath)}` })
    }

    const chunks = chunkText(fullText)
    const embeddings = await embedDocuments(chunks)
    const embeddingDims = embeddings.length ? embeddings[0].length : 0

    resetCollection(COLLECTION_NAME)
    const ids = chunks.map((_, i) => `chunk-${i}`)
    const metadatas = chunks.map((c, i) => ({
      chunk_index: i,
      char_count: c.length,
      source: path.basename(sourcePath),
    }))
    addToCollection(COLLECTION_NAME, { ids, embeddings, documents: chunks, metadatas })

    res.json({
      source_file: path.basename(sourcePath),
      source_folder: DATA_DIR,
      num_pages: numPages,
      total_characters: fullText.length,
      num_chunks: chunks.length,
      chunk_size: CHUNK_SIZE,
      chunk_overlap: CHUNK_OVERLAP,
      embedding_model: MODEL_NAME,
      embedding_dims: embeddingDims,
      sample_embedding: embeddings.length ? embeddings[0].slice(0, 8).map((v) => Math.round(v * 10000) / 10000) : [],
      chunks_preview: chunks.map((c, i) => ({
        id: ids[i],
        preview: c.slice(0, 220),
        char_count: c.length,
      })),
    })
  } catch (err) {
    res.status(err.status || 500).json({ detail: err.message })
  }
})

app.post('/api/reset', (req, res) => {
  resetCollection(COLLECTION_NAME)
  res.json({ ingested: false, num_chunks: 0 })
})

app.post('/api/query', async (req, res) => {
  const { question, top_k: topK = TOP_K } = req.body || {}
  if (!question || !question.trim()) {
    return res.status(400).json({ detail: 'Question must not be empty' })
  }

  const count = getCollectionCount(COLLECTION_NAME)
  if (count === 0) {
    return res.status(400).json({ detail: 'No documents ingested yet. Run ingestion first.' })
  }

  try {
    const queryEmbedding = await embedQuery(question)
    const matches = queryCollection(COLLECTION_NAME, queryEmbedding, topK)
    const retrievedChunks = matches.map((m) => ({
      id: m.id,
      text: m.document,
      metadata: m.metadata,
      similarity: Math.round(m.similarity * 10000) / 10000,
    }))

    const { answer, totalTokens } = await generateAnswer(question, retrievedChunks)
    const augmentedPrompt = buildAugmentedPrompt(question, retrievedChunks)

    res.json({
      question,
      retrieved_chunks: retrievedChunks,
      answer,
      model: GROQ_MODEL,
      total_tokens: totalTokens,
      augmented_prompt: augmentedPrompt,
    })
  } catch (err) {
    res.status(err.status || 500).json({ detail: err.message })
  }
})

const PORT = 8000
app.listen(PORT, () => {
  console.log(`RAG Explorer backend listening on http://localhost:${PORT}`)
})
