import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres import PGVector
from sqlalchemy import create_engine
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document

# Load environment variables
load_dotenv()

# Configuration
PDF_PATH = os.getenv("PDF_PATH", "document.pdf")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/rag?client_encoding=utf8")  # nosec
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize FastAPI app
app = FastAPI(title="PDF Ingestão API", description="API para ingestão de PDFs com embeddings")

def get_embeddings():
    """Get embeddings based on provider configuration"""
    if LLM_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY não configurada")
        return OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=OPENAI_API_KEY
        )
    elif LLM_PROVIDER == "google":
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY não configurada")
        return GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=GOOGLE_API_KEY
        )
    else:
        raise ValueError(f"Provedor não suportado: {LLM_PROVIDER}")

def get_vector_store():
    """Get vector store connection"""
    embeddings = get_embeddings()
    try:
        # Try with engine first
        engine = create_engine(
            DATABASE_URL, 
            client_encoding='utf8',
            echo=False,
            pool_pre_ping=True
        )
        return PGVector(
            embeddings=embeddings,
            connection=engine,
            collection_name="pdf_documents",
            pre_delete_collection=False
        )
    except Exception as e:
        print(f"Tentando conexão alternativa: {e}")
        # Fallback to string connection
        return PGVector(
            embeddings=embeddings,
            connection=DATABASE_URL,
            collection_name="pdf_documents",
            pre_delete_collection=False
        )

def process_pdf(pdf_path: str):
    """Process PDF and create embeddings"""
    try:
        # Check if PDF exists
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")
        
        print(f"Carregando PDF: {pdf_path}")
        
        # Load PDF
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        print(f"Documentos carregados: {len(documents)}")
        
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.split_documents(documents)
        print(f"Chunks criados: {len(chunks)}")
        
        # Get vector store
        vector_store = get_vector_store()
        
        # Add documents to vector store
        print("Adicionando documentos ao banco de dados...")
        vector_store.add_documents(chunks)
        
        print("Ingestão concluída com sucesso!")
        return {
            "status": "success",
            "message": f"PDF processado com sucesso. {len(chunks)} chunks criados.",
            "chunks_count": len(chunks)
        }
        
    except Exception as e:
        print(f"Erro durante a ingestão: {str(e)}")
        raise e

@app.get("/")
async def root():
    return {"message": "API de Ingestão de PDF - LangChain + PostgreSQL"}

@app.post("/ingest")
async def ingest_endpoint():
    """Endpoint para ingestão do PDF"""
    try:
        result = process_pdf(PDF_PATH)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        get_vector_store()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

def ingest_pdf():
    """Main function for CLI usage"""
    try:
        result = process_pdf(PDF_PATH)
        print(f"[SUCCESS] {result['message']}")
        return True
    except Exception as e:
        print(f"[ERROR] Erro na ingestão: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        # Run as FastAPI server
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        # Run as CLI script
        ingest_pdf()