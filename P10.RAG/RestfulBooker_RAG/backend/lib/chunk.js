export const CHUNK_SIZE = 800
export const CHUNK_OVERLAP = 120

export function chunkText(text, chunkSize = CHUNK_SIZE, overlap = CHUNK_OVERLAP) {
  const paragraphs = text
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter(Boolean)

  const chunks = []
  let current = ''

  for (const para of paragraphs) {
    const candidate = current ? `${current}\n\n${para}` : para
    if (candidate.length <= chunkSize) {
      current = candidate
      continue
    }

    if (current) {
      chunks.push(current)
      const tail = overlap ? current.slice(-overlap) : ''
      current = tail ? `${tail}\n\n${para}`.trim() : para
    } else {
      current = para
    }

    while (current.length > chunkSize) {
      chunks.push(current.slice(0, chunkSize))
      current = current.slice(chunkSize - overlap)
    }
  }

  if (current) chunks.push(current)

  return chunks
}
