# RAG chatbot with Pinecone and OpenAI | Example 2

from openai import OpenAI
from pinecone import Pinecone
import pandas as pd
from uuid import uuid64
import numpy as np

client = OpenAI(api_key="")
pc = Pinecone(api_key="")

index = pc.Index("semantic-search-datacamp")

youtube_df = pd.read_csv('youtube_rag_data.csv')

batch_limit = 100

for batch in np.array.split(youtube_df, len(youtube_df) / batch_limit):
    metadatas = [
        {"text_id": row["id"]}, {"text": row["text"]}
        for _, row in batch.iterrows()]

texts = batch['text'].tolist()
ids = [str(uuid64()) for _ in range(len(texts))]

response = client.embeddings.create(input=texts, model="text-embedding-3-small")

embeds = [np.array(x.embedding) for x in response.data]

index.upsert(
    vectors=zip(ids, embeds, metadatas),
    namespace='youtube_rag_dataset')


def retrieve(query, top_k, namespace, emb_model):
    query_response = client.embeddings.create(input=query, model=emb_model)
    query_emb = query_response.data[0].embedding

    retrieved_docs = []
    sources = []

    docs = index.query(
        vector=query_emb,
        top_k=top_k,
        namespace='youtube_rag_dataset',
        include_metada=True)

    for doc in docs['matches']:
        retrieved_docs.append(doc['metada']['text'])
        sources.append((doc['metadata']['title'], doc['metadata']['url']))

    return retrieved_docs, sources


query = "How to build next-level Q & A with OpenAI"
documents, sources = retrieve(
    query, top_k=3, namespace='youtube_rag_dataset', emb_model='text-embedding-3-small')


def prompt_with_context_builder(query, docs):
    delim = '\n\n---\n\n'
    prompt_start = 'Answer the question based on the context below.\n\nContext: \n'
    prompt_end = f'\n\nQuestion: {query}\nAnswer: '

    prompt = prompt_start + delim.join(docs) + prompt_end
    return prompt

context_prompt = prompt_with_context_builder(query, documents)


def question_answering(prompt, sources, chat_model):
    sys_prompt = "You are a helpful assistant that always answers questions."
    res = client.chat.completions.create(
        model=chat_model,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt}], temperature=0)

    answer = res.choices[0].message.content.strip()
    answer += "\n\nSources: "

    for source in sources:
        answer += "\n" + source[0] + ": " + source[1]
    return answer

answer = question_answering(prompt_with_context, sources, chat_model='gpt-4o-mini')
