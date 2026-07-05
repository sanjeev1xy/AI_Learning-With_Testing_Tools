import { pipeline } from '@huggingface/transformers'

const MODEL_NAME = 'nomic-ai/nomic-embed-text-v1.5'

let extractorPromise = null

function getExtractor() {
  if (!extractorPromise) {
    extractorPromise = pipeline('feature-extraction', MODEL_NAME, { dtype: 'fp32' })
  }
  return extractorPromise
}

async function embed(texts) {
  const extractor = await getExtractor()
  const output = await extractor(texts, { pooling: 'mean', normalize: true })
  return output.tolist()
}

export async function embedDocuments(chunks) {
  const prefixed = chunks.map((c) => `search_document: ${c}`)
  return embed(prefixed)
}

export async function embedQuery(text) {
  const [vector] = await embed([`search_query: ${text}`])
  return vector
}

export { MODEL_NAME }
