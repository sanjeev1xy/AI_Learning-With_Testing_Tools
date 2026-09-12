import os
import sys

from dotenv import load_dotenv
from langchain.agents import create_agent

sys.stdout.reconfigure(encoding="utf-8")  # Windows console default (cp1252) can't print LLM output
load_dotenv()
# ChatGoogleGenerativeAI looks for GOOGLE_API_KEY by default; the .env uses a custom name.
os.environ.setdefault("GOOGLE_API_KEY", os.getenv("Free_Account_Google_Gemini_API_Key", ""))

agent = create_agent(
    model="google_genai:gemini-flash-lite-latest",
    system_prompt=(
        "You are a helpful AI assistant specialized in automation testing "
        "and software development. Be clear, concise, and always think step by step."
    ),
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Who are you?"}]
})

print("Agent Response:")
print(result["messages"][-1].text)