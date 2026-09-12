from dotenv import load_dotenv
from langchain_groq import ChatGroq
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")  # Windows console default (cp1252) can't print LLM output
load_dotenv()
# ChatGroq looks for GROQ_API_KEY by default; the .env uses a custom name.
os.environ.setdefault("GROQ_API_KEY", os.getenv("Sanjeev_LangChain_Groq_API_KEY", ""))

def main():
    llm = ChatGroq(model=os.getenv("LLM_MODEL"),temperature=1)
    query = input(" Enter the question ")
    response = llm.invoke(query)
    print(response.content)

if __name__ == "__main__":
    main()
