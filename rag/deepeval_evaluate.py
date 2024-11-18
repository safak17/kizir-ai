import pandas as pd 
from datasets import Dataset
from ragas import evaluate
import ast
from ragas.metrics import LLMContextRecall, Faithfulness, FactualCorrectness
from langchain_openai.chat_models import ChatOpenAI
from ragas.llms import LangchainLLMWrapper
from langchain_ollama.embeddings import OllamaEmbeddings

from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric,ContextualPrecisionMetric,ContextualRecallMetric,ContextualRelevancyMetric,HallucinationMetric




answer_relevancy_metric = AnswerRelevancyMetric()
context_precision = ContextualPrecisionMetric()
context_recall = ContextualRecallMetric()
context_relevancy = ContextualRelevancyMetric()
#hallucination = HallucinationMetric()

questions_answers = pd.read_csv("simple_evaluation_results.csv")



test_cases = []
for index, row in questions_answers.iterrows():

    if index > 2 and index < 7 :
        continue
    test_case = LLMTestCase(
      input=row["question"],
      actual_output=row["answer"],
      retrieval_context=ast.literal_eval(row["contexts"]),
       expected_output= row["ground_truths"]
    )
    test_cases.append(test_case)

from deepeval.dataset import EvaluationDataset
dataset = EvaluationDataset(test_cases=test_cases)

dataset.evaluate([answer_relevancy_metric,context_precision,context_recall,context_relevancy])

