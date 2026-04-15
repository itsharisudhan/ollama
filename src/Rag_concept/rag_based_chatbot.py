import os

from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.Utility.load_model import load_embeddings, load_llm_model


# --------------------------------------------------
# Load Embedding Model
# --------------------------------------------------
embeddings = load_embeddings()


# --------------------------------------------------
# 1. Load PDFs
# --------------------------------------------------
def load_pdfs(pdf_path: str):

    loader = PyPDFDirectoryLoader(pdf_path)
    docs = loader.load()

    print(f"Loaded {len(docs)} pages from PDFs")

    return docs


# --------------------------------------------------
# 2. Split Documents into Chunks
# --------------------------------------------------
def split_documents(docs):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=250
    )

    chunks = splitter.split_documents(docs)

    print(f"Total Chunks Created: {len(chunks)}")

    return chunks


# --------------------------------------------------
# 3. Create / Load FAISS Vector Database
# --------------------------------------------------
def create_vector_database(documents):

    index_path = "faiss_index"

    if os.path.exists(index_path):

        print("Loading existing FAISS index...")

        db = FAISS.load_local(
            index_path,
            embeddings,
            allow_dangerous_deserialization=True
        )

    else:

        print("Creating new FAISS index...")

        db = FAISS.from_documents(documents, embeddings)

        db.save_local(index_path)

    return db


# --------------------------------------------------
# 4. Create Retriever
# --------------------------------------------------

def create_retriever(vector_db):

    retriever = vector_db.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 5,
            "fetch_k": 10
        }
    )

    return retriever

# --------------------------------------------------
# 5. Prompt Template
# --------------------------------------------------
def create_prompt():

    template = """
You are an intelligent admission assistant.

Answer the question using ONLY the provided context.

If the answer is not found in the context, respond with:
"I don't have enough information from the provided documents."

Context:
{context}

Question:
{question}

Answer:
"""

    return ChatPromptTemplate.from_template(template)


# --------------------------------------------------
# 6. Build RAG Pipeline
# --------------------------------------------------
def build_rag_chain(retriever):

    prompt = create_prompt()
    llm = load_llm_model()
    parser = StrOutputParser()

    # Create chain once
    chain = prompt | llm | parser

    def rag_chain(question: str):

        docs = retriever.invoke(question)

        if not docs:
            return "I don't have enough information from the provided documents."

        context = "\n\n".join(doc.page_content for doc in docs)

        print(f"Retrieved {len(docs)} documents")

        answer = chain.invoke({
            "context": context,
            "question": question
        })

        return answer

    return rag_chain


# --------------------------------------------------
# 7. Main Function
# --------------------------------------------------
def main():

    PDF_PATH = "src/data"

    print("Reading PDFs...")
    docs = load_pdfs(PDF_PATH)

    print("Splitting documents...")
    chunks = split_documents(docs)

    print("Setting up FAISS database...")
    vector_db = create_vector_database(chunks)

    retriever = create_retriever(vector_db)

    rag_chain = build_rag_chain(retriever)

    return rag_chain


# --------------------------------------------------
# Optional CLI Testing
# --------------------------------------------------
# if __name__ == "__main__":
#
#     rag = main()
#
#     while True:
#
#         question = input("You: ")
#
#         if question.lower() == "exit":
#             break
#
#         answer = rag(question)
#
#         print("\nBot:", answer)
#         print("-" * 50)