import Groq from 'groq-sdk'

export const GROQ_MODEL = 'openai/gpt-oss-120b'

const SYSTEM_PROMPT =
  'You are a helpful assistant answering questions about a QA Test Plan document. ' +
  'Answer ONLY using the provided context chunks. If the answer is not in the context, ' +
  "say you don't have enough information. Reference chunk numbers when relevant."

let client = null

function getClient() {
  if (!client) {
    const apiKey = process.env.GROQ_API_KEY
    if (!apiKey) {
      throw Object.assign(
        new Error('GROQ_API_KEY not set. Copy backend/.env.example to backend/.env and add your key.'),
        { status: 500 },
      )
    }
    client = new Groq({ apiKey })
  }
  return client
}

export function buildPrompt(question, retrievedChunks) {
  const context = retrievedChunks
    .map((c) => `[Chunk ${c.metadata.chunk_index}]\n${c.text}`)
    .join('\n\n')
  return `Context:\n${context}\n\nQuestion: ${question}`
}

export async function generateAnswer(question, retrievedChunks) {
  const userPrompt = buildPrompt(question, retrievedChunks)
  const groq = getClient()

  const completion = await groq.chat.completions.create({
    model: GROQ_MODEL,
    messages: [
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: userPrompt },
    ],
    temperature: 0.2,
    max_tokens: 1024,
  })

  const totalTokens = completion.usage ? completion.usage.total_tokens : 0
  return { answer: completion.choices[0].message.content, totalTokens }
}

export function buildAugmentedPrompt(question, retrievedChunks) {
  return `[SYSTEM]\n${SYSTEM_PROMPT}\n\n[USER]\n${buildPrompt(question, retrievedChunks)}`
}
