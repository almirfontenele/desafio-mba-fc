import os
from dotenv import load_dotenv
from langchain_postgres import PGVector
from sqlalchemy import create_engine
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Load environment variables
load_dotenv()

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/rag?client_encoding=utf8")  # nosec
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""

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

def get_llm():
    """Get LLM based on provider configuration"""
    if LLM_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY não configurada")
        return ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=OPENAI_API_KEY,
            temperature=0
        )
    elif LLM_PROVIDER == "google":
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY não configurada")
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=GOOGLE_API_KEY,
            temperature=0
        )
    else:
        raise ValueError(f"Provedor não suportado: {LLM_PROVIDER}")

def get_vector_store():
    """Get vector store connection"""
    embeddings = get_embeddings()
    # Create engine explicitly to handle encoding
    engine = create_engine(DATABASE_URL, client_encoding='utf8')
    return PGVector(
        embeddings=embeddings,
        connection=engine,
        collection_name="pdf_documents",
        pre_delete_collection=False
    )

def search_documents(query: str, k: int = 10):
    """Search for similar documents in the vector store"""
    try:
        vector_store = get_vector_store()
        results = vector_store.similarity_search_with_score(query, k=k)
        return results
    except Exception as e:
        print(f"Erro na busca: {str(e)}")
        return []

def format_context(documents):
    """Format documents into context string"""
    if not documents:
        return "Nenhum contexto encontrado."
    
    context_parts = []
    for i, (doc, score) in enumerate(documents, 1):
        context_parts.append(f"[{i}] {doc.page_content}")
    
    return "\n\n".join(context_parts)

def search_prompt():
    """Create search chain with prompt template"""
    try:
        # Get LLM
        llm = get_llm()
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        
        # Create chain
        chain = (
            {"contexto": lambda x: format_context(search_documents(x["pergunta"])), "pergunta": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        
        return chain
        
    except Exception as e:
        print(f"Erro ao criar chain de busca: {str(e)}")
        return None

def search_and_answer(question: str):
    """Search for documents and generate answer"""
    try:
        # Search for similar documents
        documents = search_documents(question, k=10)
        
        if not documents:
            return "Não tenho informações necessárias para responder sua pergunta."
        
        # Format context
        context = format_context(documents)
        
        # Get LLM
        llm = get_llm()
        
        # Create prompt
        prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        
        # Create chain
        chain = prompt | llm | StrOutputParser()
        
        # Generate answer
        response = chain.invoke({"contexto": context, "pergunta": question})
        
        return response
        
    except Exception as e:
        print(f"Erro na busca e resposta: {str(e)}")
        return "Erro interno. Tente novamente."

if __name__ == "__main__":
    # Test the search functionality
    test_question = "Qual o faturamento da Empresa SuperTechIABrazil?"
    result = search_and_answer(test_question)
    print(f"Pergunta: {test_question}")
    print(f"Resposta: {result}")