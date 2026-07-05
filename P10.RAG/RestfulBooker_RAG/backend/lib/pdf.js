import fs from 'fs'
import path from 'path'
import { PDFParse } from 'pdf-parse'

export const SUPPORTED_EXTENSIONS = new Set(['.pdf', '.txt'])

export function findSourceDocument(dataDir) {
  const files = fs
    .readdirSync(dataDir)
    .filter((name) => SUPPORTED_EXTENSIONS.has(path.extname(name).toLowerCase()))
    .map((name) => {
      const fullPath = path.join(dataDir, name)
      return { fullPath, mtime: fs.statSync(fullPath).mtimeMs }
    })

  if (files.length === 0) {
    throw Object.assign(new Error(`No .pdf or .txt file found in ${dataDir}. Upload a document first.`), {
      status: 404,
    })
  }

  files.sort((a, b) => b.mtime - a.mtime)
  return files[0].fullPath
}

async function readPdf(filePath) {
  const buffer = fs.readFileSync(filePath)
  const parser = new PDFParse({ data: buffer })
  try {
    const result = await parser.getText()
    return { text: result.text.trim(), numPages: result.total }
  } finally {
    await parser.destroy()
  }
}

function readTxt(filePath) {
  const text = fs.readFileSync(filePath, 'utf-8')
  return { text, numPages: 1 }
}

export async function readDocument(filePath) {
  const ext = path.extname(filePath).toLowerCase()
  if (ext === '.pdf') return readPdf(filePath)
  if (ext === '.txt') return readTxt(filePath)
  throw new Error(`Unsupported file type: ${ext}`)
}
