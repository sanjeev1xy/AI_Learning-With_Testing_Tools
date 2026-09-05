# DeepEval

# Create virtual Environment i.e venv

python -m venv venv

* Now Activate that

venv\Scripts\Activate.ps1

* then You should see:

(venv) PS C:\Users\sanje\AI_Projects_Section\P19.DeepEval>

## Pre-Requisites

* Python Installed
* Basic pytest knowledge
* LLM API Key:

  * OpenAI API Key
  * DeepSeek API Key
  * Groq API Key
  * Claude API ($5)
* Free LLM options:

  * NVIDIA API – Free
  * AMD API – Free/Limited

---

## Installation of DeepEval

### 1. Create Virtual Environment

python3 -m venv venv

### 2. Activate Virtual Environment

Linux/Mac:

source venv/bin/activate

Windows PowerShell:

venv\Scripts\Activate.ps1

### 3. Upgrade pip

python -m pip install --upgrade pip

### 4. Install DeepEval and Requests

python -m pip install -U deepeval requests

## Error: `ModuleNotFoundError: No module named 'deepeval'`

### Why is this error coming?

`deepeval` is **not installed in the current Python environment**.

### How to resolve?

Run:

python -m pip install deepeval

Then verify:

python -c "import deepeval, requests; print(deepeval.__version__, requests.__version__)"

If it still fails, check:

python -m pip show deepeval

In short: Install `deepeval` in the same Python environment that you are using to run your test.

## Verify Installation

python -c "import deepeval, requests; print(deepeval.__version__, requests.__version__)"

Expected result:

DeepEval_Version Requests_Version

## Deactivate Virtual Environment

When finished:

deactivate

# Pick the Judge LLM

DeepEval evaluates your output using a **second LLM (Judge LLM)**.

Configure the Judge LLM once.

## Groq

Groq provides an OpenAI-compatible API.

> Note: `deepeval set-grok` refers to xAI Grok, not Groq.com.

deepeval set-local-model \
  --model openai/gpt-oss-120b \
  --base-url "https://api.groq.com/openai/v1" \
  --format json \
  --prompt-api-key

## OpenAI

export OPENAI_API_KEY=your-api-key
deepeval set-openai --model gpt-4o-mini

You can use:

--save dotenv:.env.local

to persist the API key.

Switch back with:

deepeval unset-local-model

# Run DeepEval Test

pytest test_01_Anwser_Relevancy.py

# Important: Watch Out

* Every metric assertion can make a real LLM API call.
* API calls may incur cost depending on the provider/model.
* Keep the golden dataset small during development.
* Never commit API keys to Git.

### Keep these files/folders out of Git:

.env
.env.local
venv/
.deepeval/

Golden Rule:
Install → Verify → Configure Judge LLM → Run pytest
