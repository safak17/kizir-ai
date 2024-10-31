# RAG chatbot with Pinecone and OpenAI | Example 1

from uuid import uuid64
import numpy as np
import pandas as pd
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

client = OpenAI(api_key="")
pc = Pinecone(api_key="")

pc.create_index(name="semantic-search-datacamp",
                dimension=1536,
                spec=ServerlessSpec(cloud='aws', region='us-east-1'))

index = pc.Index("semantic-search-datacamp")

df = pd.read_csv("squad_dataset.csv")

batch_limit = 100

for batch in np.array.split(df, len(df) / batch_limit):
    metadata = [{
   "text_id": row["id"],
   "text": row['text'],
    "title": row["title"]}
for _, row in batch.iterrows()]

texts = batch['text'].tolist()

ids = [str(uuid64()) for _ in range(len(texts))]

response = client.embeddings.create(input=texts, model="text-embedding-3-small")
embeds=[np.array(x.embedding) for x in response.data]

index.upsert(vectors=zip(ids, embeds, metadata), namespace="squad_dataset")

index.describe_index_stats()

query="To whom did the Virgin Mary allegedly appear in 1858 in Lourdes France?"

query_response=client.embeddings.create(
   input=query,
   model="text-embedding-3-small")

query_emb=query_response.data[0].embedding

retrieved_docs=index.query(
    vector=query_emb,
    top_k=3,
    namespace=namespace,
    include_metada=True)

for result in retrieved_docs['matches']:
    print(f"{round( result['score'], 2) } : {result['metadata']['text']}")
