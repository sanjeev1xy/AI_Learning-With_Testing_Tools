"""Query rewriting + grounded generation, via Groq (openai/gpt-oss-120b).

The original spec called for OpenRouter (deepseek) here; this build
substitutes Groq throughout since that's the only LLM API key configured
in this repo.
"""
import json
import re

from groq import Groq

from . import config

_client = None

GENERATE_TRIGGERS = re.compile(
    r"\b(create|generate|write|draft)\b.{0,40}\b(test case|testcase)\b", re.IGNORECASE
)


def get_client():
    global _client
    if _client is None:
        if not config.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY not set. Copy .env.example to .env and add your key.")
        _client = Groq(api_key=config.GROQ_API_KEY)
    return _client


def detect_mode(question):
    return "generate" if GENERATE_TRIGGERS.search(question) else "answer"


def rewrite_query(question, n=3):
    """Returns a list of n phrasings, the first of which is the original question."""
    if not config.REWRITE_ENABLED:
        return [question]

    client = get_client()
    prompt = (
        f"Generate {n - 1} alternate phrasings of this QA-test-case search query. "
        "Keep the same meaning, vary the wording. Return ONLY a JSON array of strings, "
        f"no other text.\n\nQuery: {question}"
    )
    completion = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=300,
    )
    raw = completion.choices[0].message.content.strip()
    try:
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        alternates = json.loads(match.group(0)) if match else []
    except (json.JSONDecodeError, AttributeError):
        alternates = []

    variants = [question] + [a for a in alternates if isinstance(a, str)]
    return variants[:n] if len(variants) >= n else variants


ANSWER_SYSTEM_PROMPT = (
    "You are a QA test-case assistant for The Testing Academy. Answer ONLY using "
    "the provided context chunks (each tagged [Chunk N]). If the answer isn't in "
    "the context, say so plainly. Cite chunks inline like [Chunk 2]."
)

GENERATE_SYSTEM_PROMPT = (
    "You are a QA test-case author. Using the retrieved similar test cases as style "
    "templates, draft ONE new test case for the user's request. Respond in this exact "
    "structure:\n\nTitle:\nPreconditions:\nSteps:\nExpected:\nPriority:\nTags:\n\n"
    "Keep it concise and consistent with the style of the retrieved examples."
)


def build_context(chunks):
    return "\n\n".join(f"[Chunk {i}]\n{c['text']}" for i, c in enumerate(chunks))


def generate_answer(question, chunks, mode="answer"):
    context = build_context(chunks)
    system_prompt = GENERATE_SYSTEM_PROMPT if mode == "generate" else ANSWER_SYSTEM_PROMPT
    user_prompt = f"Context:\n{context}\n\nRequest: {question}"

    client = get_client()
    completion = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=1200,
    )
    total_tokens = completion.usage.total_tokens if completion.usage else 0
    return completion.choices[0].message.content, total_tokens
