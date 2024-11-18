from langchain_community.llms import LlamaCpp
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler
from langchain_core.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.messages import AIMessage, HumanMessage
import pandas as pd
import json
from rag_simple import CourseRecommendationAssistant


with open("evaluate_test_cases.json", "r") as file:
    questions_json = json.load(file)

# Interaction loop
results_df = pd.DataFrame(columns=["question", "contexts", "answer"])

assistant = CourseRecommendationAssistant(
    model_path="models/gemma-2-9b-it-Q8_0.gguf",
    embedding_model_name="sentence-transformers/all-MiniLM-L6-v2",
    vectorstore_path="faiss_index"
)
for question_json in  questions_json:
    response,docs = assistant.evaluate(question_json["question"])
    
    results_df = pd.concat([results_df, pd.DataFrame([{
        "question": question_json["question"],
        "contexts": [doc.page_content for doc in docs],
        "answer": response,
        "ground_truths": question_json["ground_truths"]
    }])], ignore_index=True)
   
results_df.to_csv("simple_evaluation_results.csv", index=False)