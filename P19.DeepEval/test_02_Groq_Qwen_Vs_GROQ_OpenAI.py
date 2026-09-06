#Flow:
# 1. Send "What is 2+2?" to Groq Qwen3.8-27b (the model under test).
# 2. Capture the raw answer.
# 3. Hand input + answer + context to DeepEval.
# 4. openai/gpt-oss-120b as judge -> scores AnswerRelevancy + Hallucination.
#    Subject != judge on purpose: a judge scoring its own family inflates scores.

GROQ_MODEL = "qwen/qwen3.8-27b"
JUDGE_MODEL = "openai/gpt-oss-120b"

import os
import sys

# --- Environment setup: must run BEFORE `import deepeval` ---------------------
# deepeval reads its settings from os.environ at import time, and it only
# autoloads .env / .env.local from the shell's cwd. Load them relative to this
# file instead, so the command works from the repo root too, and make sure the
# judge config lands in os.environ before deepeval is imported.
from dotenv import load_dotenv

_HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_HERE, ".env"))        # -> DeepEvaluation_* keys
load_dotenv(os.path.join(_HERE, ".env.local"))  # -> USE_LOCAL_MODEL / LOCAL_MODEL_*

# The Groq key (gsk_...) may be under any of these names depending on the file.
GROQ_API_KEY = (
    os.getenv("LOCAL_MODEL_API_KEY")
    or os.getenv("OPENAI_API_KEY")
    or os.getenv("DeepEvaluation_Groq_API_KEY")
)
if not GROQ_API_KEY:
    sys.exit("No Groq API key found in .env / .env.local")

# Point deepeval's judge at Groq's OpenAI-compatible endpoint as a "local model"
# regardless of cwd. `model=JUDGE_MODEL` strings passed to the metrics below then
# route to this LocalModel instead of api.openai.com.
os.environ["USE_LOCAL_MODEL"] = "YES"
os.environ["LOCAL_MODEL_NAME"] = JUDGE_MODEL
os.environ["LOCAL_MODEL_BASE_URL"] = "https://api.groq.com/openai/v1"
os.environ["LOCAL_MODEL_API_KEY"] = GROQ_API_KEY
os.environ["LOCAL_MODEL_FORMAT"] = "json"
os.environ["OPENAI_API_KEY"] = GROQ_API_KEY  # some deepeval paths still read this

# Windows consoles default to cp1252; deepeval's rich progress bar prints emoji
# (the target glyph) and crashes with UnicodeEncodeError. Force UTF-8 on the
# real streams. No-op where already UTF-8 or captured (e.g. pytest without -s).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    except (AttributeError, ValueError):
        pass
# ----------------------------------------------------------------------------

from openai import OpenAI

from deepeval.metrics import AnswerRelevancyMetric, HallucinationMetric
from deepeval.models import LocalModel
from deepeval.test_case import LLMTestCase
from deepeval import assert_test

# Groq speaks the OpenAI API, so the official openai SDK works unchanged:
# just point base_url at Groq.
groq = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)


def llm_response(question):
    """Ask GROQ_MODEL one question and return its raw answer text."""
    response = groq.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": question}],
        # temperature=0 keeps the answer stable so the score below is
        # reproducible. The judge is still non-deterministic; this only
        # pins the thing under test.
        temperature=0,
        # qwen3 is a reasoning model. reasoning_effort="none" drops the
        # <think> block and max_tokens caps output so the request stays
        # under Groq free-tier OTPM (1000 output tokens/min for this model).
        max_tokens=100,
        reasoning_effort="none",
    )
    return response.choices[0].message.content.strip()

question = "What is 2+2? Reply with just the number."
answer = llm_response(question)
print(f"\n[Groq {GROQ_MODEL}] -> {answer!r}\n")



# Explicit judge instance -> deepeval treats it as a native model and skips the
# cwd/plugin-dependent USE_LOCAL_MODEL lookup that otherwise sends the string
# "openai/gpt-oss-120b" to api.openai.com and 401s on the Groq key.
judge = LocalModel(
    model=JUDGE_MODEL,
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)


def test_l4_with_judge_qwen():
    case = LLMTestCase(
        input=question,
        actual_output=answer,
        expected_output="4",
        # HallucinationMetric scores actual_output against this grounding text.
        context=["Basic arithmetic fact: 2 + 2 = 4"],
    )

    metrics = [
        AnswerRelevancyMetric(threshold=0.8, model=judge),
        HallucinationMetric(threshold=0.3, model=judge),
    ]
    assert_test(case, metrics)
