I want you to create a simple RAG Explorer application.
The source files will be available in the data folder. I will provide a simple PDF file, which is a Test Plan Document for Restful Booker API.
Your task is to build a React-based UI that demonstrates how the ingestion and retrieval process works.
The application should do the following:

Read the PDF file from the data/data folder.
Split the PDF content into chunks.
Generate embeddings for those chunks using the Nomic Embed embedding model.
Store the embeddings automatically in a local ChromaDB instance.
Provide a query interface where I can ask questions related to the PDF.
For every query, retrieve and display the top 4 relevant chunks fetched from the document.
Use Groq as the LLM provider, with the OpenGPT 120B model, to generate the final answer based on the retrieved chunks.
The UI should clearly showcase the complete RAG flow: PDF ingestion, chunking, embedding, storage, retrieval, and answer generation.

The goal of this application is to demonstrate how a basic RAG pipeline works end-to-end using a local vector database and a React frontend.