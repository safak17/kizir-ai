
from langchain_community.llms import LlamaCpp
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler
from langchain_core.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.messages import AIMessage, HumanMessage
import pandas as pd
import json
from rag_simple import CourseRecommendationAssistant
import numpy as np

import time

with open("evaluate_test_cases.json", "r") as file:
    questions_json = json.load(file)

# Interaction loop
results_df = pd.DataFrame(columns=["question", "contexts", "answer"])

assistant = CourseRecommendationAssistant(
    model_path="models/gemma-2-9b-it-Q8_0.gguf",
    embedding_model_name="sentence-transformers/all-MiniLM-L6-v2",
    vectorstore_path="faiss_index"
)
tokens_per_second_overall = []
for question_json in  questions_json:
    start_time = time.time()
    response,tokens_per_sec = assistant.performance_metrics(question_json["question"])
    tokens_per_second_overall.append(tokens_per_sec)

print(f"Tokens per second averaged over {len(questions_json)} requests is {np.mean(tokens_per_second_overall)}")

