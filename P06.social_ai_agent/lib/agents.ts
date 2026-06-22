import Groq from 'groq-sdk';
import { GoogleGenAI } from '@google/genai';
import { writeFile, mkdir } from 'fs/promises';
import path from 'path';
import { excelManager } from './excelManager';
import type { StatusType } from './types';

const KEYWORD_POOL = [
  'QA', 'MCP', 'RAG', 'LLM', 'AI Agents', 'n8n', 'LangFlow',
  'Crew AI', 'DeepEval', 'LangChain', 'AI Harness', 'LLM Eval',
];

export function todayISO(): string {
  return new Date().toISOString().split('T')[0];
}

function getGroq(): Groq {
  const apiKey = process.env.GROQ_API_KEY;
  if (!apiKey) throw new Error('GROQ_API_KEY not set in .env.local');
  return new Groq({ apiKey });
}

function getGemini(): GoogleGenAI {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) throw new Error('GEMINI_API_KEY not set in .env.local');
  return new GoogleGenAI({ apiKey });
}

async function groqChat(
  groq: Groq,
  system: string,
  user: string,
  maxTokens: number,
  model = 'llama-3.3-70b-versatile',
): Promise<string> {
  const res = await groq.chat.completions.create({
    model,
    temperature: 0.7,
    max_tokens: maxTokens,
    messages: [
      { role: 'system', content: system },
      { role: 'user', content: user },
    ],
  });
  const text = res.choices[0]?.message?.content?.trim() ?? '';
  if (!text) throw new Error('Groq returned empty content');
  return text;
}

// ─── Agent 1: Topic Generator ─────────────────────────────────────────────────
export async function agent1TopicGenerator(): Promise<string> {
  const today = todayISO();

  // Idempotent: if row already exists, return its topic
  const existing = await excelManager.getRowByDate(today);
  if (existing) return existing.topic;

  const groq = getGroq();
  const allRows = await excelManager.getAllRows();
  const used = allRows.map((r) => r.topic).filter(Boolean);

  const topic = await groqChat(
    groq,
    'You are a senior technical content strategist. Return ONLY the topic title — no quotes, no explanation, no leading text.',
    `Generate ONE unique, specific, and actionable content topic title related to one of these keywords: ${KEYWORD_POOL.join(', ')}.

Topics already covered (do not repeat or closely paraphrase):
${used.length ? used.map((t) => `- ${t}`).join('\n') : '(none yet)'}

The title should be specific and practical, e.g. "Building a RAG Pipeline with LangChain and Pinecone" — not just "RAG".`,
    100,
    'llama-3.1-8b-instant',
  );

  await excelManager.appendRow({ date: today, topic, status: 'Pending' });
  console.log(`[Agent1] Topic created: ${topic}`);
  return topic;
}

// ─── Agent 2: Content Writer ──────────────────────────────────────────────────
export async function agent2ContentWriter(topic: string): Promise<void> {
  const today = todayISO();
  const groq = getGroq();

  await excelManager.updateRow(today, { status: 'Writing' as StatusType });

  const SYSTEM = `You are a senior software engineer and opinionated technical writer.
Rules:
- Short paragraphs (2-4 sentences max).
- Real, specific examples — not vague descriptions.
- No filler: never use "game-changer", "dive deep", "leverage", "cutting-edge", "unleash", "empower".
- Direct voice. Say what you mean.
- Assume the reader is a working engineer, not a beginner.`;

  console.log('[Agent2] Writing LinkedIn post…');
  const linkedinPost = await groqChat(
    groq,
    SYSTEM,
    `Write a LinkedIn post about: "${topic}"
- First line must be a specific, provocative hook (no "I'm excited to share").
- 150-200 words total.
- Short lines — LinkedIn collapses long paragraphs.
- End with 2-3 relevant hashtags on a separate line.
- No emojis.`,
    400,
  );

  console.log('[Agent2] Writing Medium article…');
  const mediumArticle = await groqChat(
    groq,
    SYSTEM,
    `Write a ~3000-word Medium article about: "${topic}"
Format (Markdown):
- TL;DR (3 bullet points) at the very top
- ## Introduction
- ## [Section 1 relevant title]
- ## [Section 2 relevant title]
- ## [Section 3 relevant title]
- ## [Section 4 practical example or code walkthrough]
- ## Conclusion + Key Takeaways

Include code examples in triple-backtick blocks where relevant. Use real tool names and library versions.`,
    4500,
  );

  console.log('[Agent2] Writing Instagram script…');
  const igScript = await groqChat(
    groq,
    SYSTEM,
    `Write an Instagram carousel/reel script about: "${topic}"
Format:
Slide 1 (Hook): [Punchy single-sentence hook that stops the scroll]
Slide 2: [Title + 2-3 bullet points]
Slides 3-7: [One concept per slide — short title + 2-3 bullet points]
Slide 8 (CTA): [Follow + specific action for the viewer]

Mobile-first language. Each slide fits on screen. No jargon dump.`,
    800,
  );

  console.log('[Agent2] Writing YouTube script…');
  const ytScript = await groqChat(
    groq,
    SYSTEM,
    `Write a YouTube video script about: "${topic}" (target: 12-15 minute video).
Format:
[0:00] INTRO — Hook (state the exact problem this video solves) + what viewer will learn + brief credibility
[1:30] SECTION 1 — [title] — main content
[4:00] SECTION 2 — [title]
[7:30] SECTION 3 — [title]
[11:00] SECTION 4 — [title] (demo/code walkthrough)
[13:30] OUTRO — 3 key takeaways + subscribe CTA + related video mention

Add [B-roll: description] annotations for visual suggestions. Write for spoken delivery — conversational but precise.`,
    2000,
  );

  console.log('[Agent2] Writing Dev.to article…');
  const devtoArticle = await groqChat(
    groq,
    SYSTEM,
    `Write a ~2000-word Dev.to technical article about: "${topic}"
Format (Markdown):
---
title: [article title]
tags: [comma-separated relevant tags]
---

## The Problem
## [Main concept]
## Implementation (with \`\`\` code blocks)
## [Advanced pattern or gotcha]
## Key Takeaways

Audience: engineers building production systems. Include real code examples, specific library names and versions, and links described as [Resource Name](URL) even if URL is illustrative.`,
    3000,
  );

  await excelManager.updateRow(today, {
    linkedinPost,
    mediumArticle,
    igScript,
    ytScript,
    devtoArticle,
    status: 'Imaging' as StatusType,
  });

  console.log('[Agent2] Content writing complete.');
}

// ─── Agent 3: Image Generator ────────────────────────────────────────────────
// Strategy:
//   1. Try Gemini native image generation (requires paid-tier model access).
//   2. Fall back to Pollinations.ai (free, FLUX-based, no API key) automatically.
// Result: images always generate regardless of Gemini tier.

const GEMINI_IMAGE_MODELS = [
  'gemini-2.0-flash-preview-image-generation',
  'gemini-2.0-flash-exp-image-generation',
];

async function tryGeminiImage(
  gemini: GoogleGenAI,
  prompt: string,
  outputPath: string,
): Promise<string> {
  let lastErr: Error = new Error('No Gemini image models tried');

  for (const model of GEMINI_IMAGE_MODELS) {
    try {
      const response = await gemini.models.generateContent({
        model,
        contents: [{ role: 'user', parts: [{ text: prompt }] }],
        config: { responseModalities: ['IMAGE'] },
      });

      const parts = response.candidates?.[0]?.content?.parts ?? [];
      let imageBase64: string | undefined;
      for (const part of parts) {
        if (part.inlineData?.data) { imageBase64 = part.inlineData.data; break; }
      }
      if (!imageBase64) throw new Error('Empty image response');

      const buffer = Buffer.from(imageBase64, 'base64');
      await mkdir(path.dirname(outputPath), { recursive: true });
      await writeFile(outputPath, buffer);
      console.log(`[Agent3] Gemini image saved via ${model}`);
      return outputPath;
    } catch (err) {
      lastErr = err instanceof Error ? err : new Error(String(err));
      console.warn(`[Agent3] ${model} unavailable: ${lastErr.message.slice(0, 80)}`);
    }
  }
  throw lastErr;
}

async function pollinations(
  prompt: string,
  width: number,
  height: number,
  outputPath: string,
): Promise<string> {
  const encoded = encodeURIComponent(
    `${prompt} professional, dark background, geometric, no text, vibrant colours`,
  );
  const url = `https://image.pollinations.ai/prompt/${encoded}?width=${width}&height=${height}&nologo=true&model=flux&seed=${Date.now()}`;
  console.log(`[Agent3] Pollinations → ${url.slice(0, 100)}…`);

  const res = await fetch(url, { signal: AbortSignal.timeout(60_000) });
  if (!res.ok) throw new Error(`Pollinations HTTP ${res.status}`);

  const buf = Buffer.from(await res.arrayBuffer());
  await mkdir(path.dirname(outputPath), { recursive: true });
  await writeFile(outputPath, buf);
  return outputPath;
}

async function generateImage(
  gemini: GoogleGenAI,
  prompt: string,
  outputPath: string,
  width: number,
  height: number,
): Promise<string> {
  try {
    return await tryGeminiImage(gemini, prompt, outputPath);
  } catch {
    console.log('[Agent3] Gemini image generation not available — using Pollinations.ai fallback');
    return pollinations(prompt, width, height, outputPath);
  }
}

export async function agent3ImageGenerator(topic: string): Promise<void> {
  const today = todayISO();
  const gemini = getGemini();
  const stamp = today.replace(/-/g, '');
  const imagesDir = path.join(process.cwd(), 'public', 'images');

  const BASE =
    `Tech illustration for: "${topic}". ` +
    'Dark background, clean geometric style, vibrant indigo and teal accents, high detail.';

  try {
    console.log('[Agent3] Generating Medium cover (1920×1080)…');
    const mediumPath = await generateImage(
      gemini,
      `${BASE} Wide horizontal blog hero banner.`,
      path.join(imagesDir, `medium-${stamp}.jpg`),
      1920, 1080,
    );

    console.log('[Agent3] Generating LinkedIn image (1200×627)…');
    const linkedinPath = await generateImage(
      gemini,
      `${BASE} LinkedIn post horizontal banner.`,
      path.join(imagesDir, `linkedin-${stamp}.jpg`),
      1200, 627,
    );

    console.log('[Agent3] Generating Instagram square (1080×1080)…');
    const igPath = await generateImage(
      gemini,
      `${BASE} Instagram square post, bold eye-catching composition.`,
      path.join(imagesDir, `ig-${stamp}.jpg`),
      1080, 1080,
    );

    const rel = (p: string) => `/images/${path.basename(p)}`;

    await excelManager.updateRow(today, {
      mediumImage: rel(mediumPath),
      linkedinImage: rel(linkedinPath),
      igImage: rel(igPath),
      status: 'Done' as StatusType,
    });

    console.log('[Agent3] All images saved → Status: Done');
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error('[Agent3] Image generation failed:', msg);
    await excelManager.updateRow(today, { status: 'Error' as StatusType });
    throw err;
  }
}
