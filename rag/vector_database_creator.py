from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
from sentence_transformers import SentenceTransformer
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import pandas as pd
import faiss

#model = SentenceTransformer('all-MiniLM-L6-v2',device="cuda:0")
#embeddings = HuggingFaceEmbeddings(model_name ='sentence-transformer/all-MiniLM-L6-v2')
model_kwargs = {'device': 'cuda:0'}
embeddings = HuggingFaceEmbeddings(model_name ='sentence-transformers/all-MiniLM-L6-v2',model_kwargs=model_kwargs)
#df = pd.read_csv("../analysis/example_structured.csv")
df = pd.read_csv("combined_merged.csv")
df['merged_text'] = (
    df['Course Name'].fillna('') + ' ' +
    df['Course Objectives'].fillna('') + ' ' +
    df['Course Learning Outcomes'].fillna('') + ' ' +
    df['Course Content'].fillna('')
)

documents = [
    Document(page_content=row['merged_text'], metadata={'Course Code': row['Course Code'],'Day1': row['Day1'],'Start Hour1': row['Start Hour1'], 'End Hour1': row['End Hour1'], 'Instructor Name': row['Instructor Name'], 'Prerequisite' : row['Prerequisite'] })
    for _, row in df.iterrows()
]


vectorstore = FAISS.from_documents(documents,embeddings)



# Example query
query = "courses about games"
query_embedding = embeddings.embed_query(query)

# Perform similarity search
similar_docs = vectorstore.similarity_search_by_vector(query_embedding, k=5)

# Display results
for doc in similar_docs:
    print("Course Code:", doc.metadata['Course Code'])
    print("Content:", doc.page_content)
    print("----")


vectorstore.save_local("faiss_index")



