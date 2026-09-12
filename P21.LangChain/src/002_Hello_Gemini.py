import os
import sys

from dotenv import load_dotenv
from langchain.agents import create_agent

sys.stdout.reconfigure(encoding="utf-8")  # Windows console default (cp1252) can't print LLM output
load_dotenv()
# ChatGoogleGenerativeAI looks for GOOGLE_API_KEY by default; the .env uses a custom name.
os.environ.setdefault("GOOGLE_API_KEY", os.getenv("Free_Account_Google_Gemini_API_Key", ""))

def main():
    agent = create_agent(model=os.environ["GEMINI_LLM_MODEL"])
    query = input("Ask your question: ")
    result = agent.invoke({"messages": [("user", query)]})
    print(result["messages"][-1].text)

if __name__ == "__main__":
    main()
