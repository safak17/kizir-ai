from sentence_transformers import SentenceTransformer
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
import pandas as pd
import faiss
import re
from typing import List
import os

# Initialize embeddings
model_kwargs = {'device': 'cuda:0'}
embeddings = HuggingFaceEmbeddings(model_name='TaylorAI/gte-tiny', model_kwargs=model_kwargs)

# Function to chunk text with overlap
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into smaller chunks with overlap.

    Args:
        text: The input text to be chunked.
        chunk_size: Maximum size of each chunk.
        overlap: Number of words to overlap between chunks.

    Returns:
        List of text chunks.
    """
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(' '.join(words[start:end]))
        start += chunk_size - overlap  # Move start with overlap
    return chunks

# Parse articles from the text file

def parse_program_details(text: str, text_name: str, chunk_size: int = 500, overlap: int = 50) -> List[Document]:
    """
    Parse the provided text into chunks and add metadata.

    Args:
        text: The input text to be parsed.
        text_name: The name of the text (used as metadata).
        chunk_size: Maximum size of each chunk.
        overlap: Number of words to overlap between chunks.

    Returns:
        List of Document objects.
    """
    documents = []
    chunks = chunk_text(text, chunk_size, overlap)
    for idx, chunk in enumerate(chunks):
        documents.append(
            Document(
                page_content=text_name + " " + text_name  + " Graduate Program Details: " + chunk,
                metadata={
                    "Title": text_name,
                    "Details": text_name + " Graduate Program Details",
                    "Part": idx + 1
                }
            )
        )
    return documents

def process_text_files(folder_path: str, chunk_size: int = 500, overlap: int = 50) -> List[Document]:
    """
    Process all text files in a folder and parse them into Document objects.

    Args:
        folder_path: Path to the folder containing text files.
        chunk_size: Maximum size of each chunk.
        overlap: Number of words to overlap between chunks.

    Returns:
        List of Document objects.
    """
    documents = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.txt'):  # Process only .txt files
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            # Use the file name (without extension) as the text_name, removing underscores
            text_name = os.path.splitext(file_name)[0].replace('_', ' ')
            # Parse the text and add to the documents list
            documents.extend(parse_program_details(text, text_name, chunk_size, overlap))
    return documents

    
def parse_articles(file_path: str, chunk_size: int = 500, overlap: int = 50) -> List[Document]:
    """
    Parse the articles from a text file and create Document objects.

    Args:
        file_path: Path to the text file containing articles.
        chunk_size: Maximum size of each chunk.
        overlap: Number of words to overlap between chunks.

    Returns:
        List of Document objects.
    """
    documents = []
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Regular expression to split articles based on "ARTICLE <number>" pattern
    articles = re.split(r"(ARTICLE \d+\s*[-–—])", content)
    for i in range(1, len(articles), 2):
        article_title = articles[i].strip()
        article_content = articles[i + 1].strip()
        chunks = chunk_text(article_content, chunk_size, overlap)
        for idx, chunk in enumerate(chunks):
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={"Title": "METU Graduate Regulations " + article_title, "Part": idx + 1}  # Metadata can include part numbers for chunks
                )
            )
    return documents

# Load the CSV data

df = pd.read_csv("combined_merged.csv")
df['merged_text'] = (
    df['Course Name'].fillna('') + ' ' +
    df['Course Objectives'].fillna('') + ' ' +
    df['Course Learning Outcomes'].fillna('') + ' ' +
    df['Course Content'].fillna('')
)

# Combine CSV documents
documents = [
    Document(
        page_content=row['merged_text'], 
        metadata={
            'Course Code': row['Course Code'],
            'Day1': row['Day1'],
            'Start Hour1': row['Start Hour1'], 
            'End Hour1': row['End Hour1'], 
            'Instructor Name': row['Instructor Name'], 
            'Prerequisite': row['Prerequisite']
        }
    ) 
    for _, row in df.iterrows()
]


# Parse and add articles as separate documents
articles_file = "regulations.txt"  # Replace with the actual path to your text file
documents += parse_articles(articles_file, chunk_size=500, overlap=50)

documents += process_text_files("program_details/")


vectorstore = FAISS.from_documents(documents, embeddings)

# Example query
query = "Data Informatics graduate program ?"
query_embedding = embeddings.embed_query(query)

# Perform similarity search
similar_docs = vectorstore.similarity_search_by_vector(query_embedding, k=20)

# Display results
for doc in similar_docs:
    print("Metadata:", doc.metadata)
    print("Content:", doc.page_content)
    print("----")

# Save the FAISS index
vectorstore.save_local("faiss_index_regulations_added_gte")

