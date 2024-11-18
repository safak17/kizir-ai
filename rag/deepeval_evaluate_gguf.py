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

from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.models.base_model import DeepEvalBaseLLM
from llama_cpp import Llama, LlamaGrammar

import json
from pydantic import BaseModel
import torch
from lmformatenforcer import JsonSchemaParser
from lmformatenforcer.integrations.transformers import (
    build_transformers_prefix_allowed_tokens_fn,
)
from transformers import BitsAndBytesConfig
from transformers import AutoModelForCausalLM, AutoTokenizer
import transformers
from deepeval.models import DeepEvalBaseLLM


class CustomMistral7B(DeepEvalBaseLLM):
    def __init__(self):
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )

        model_4bit = AutoModelForCausalLM.from_pretrained(
            "mistralai/Mistral-7B-Instruct-v0.3",
            device_map="cuda:0",
            #quantization_config=quantization_config,
        )
        tokenizer = AutoTokenizer.from_pretrained(
            "mistralai/Mistral-7B-Instruct-v0.3"
        )

        self.model = model_4bit
        self.tokenizer = tokenizer

    def load_model(self):
        return self.model

    def generate(self, prompt: str, schema: BaseModel) -> BaseModel:
        model = self.load_model()
        pipeline = transformers.pipeline(
            "text-generation",
            model=model,
            tokenizer=self.tokenizer,
            use_cache=True,
            device_map="cuda:0",
            max_length=8192,
            do_sample=False,
            top_k=1,
            num_return_sequences=1,
            eos_token_id=self.tokenizer.eos_token_id,
            pad_token_id=self.tokenizer.eos_token_id,
        )

        # Create parser required for JSON confinement using lmformatenforcer
        parser = JsonSchemaParser(schema.schema())
        prefix_function = build_transformers_prefix_allowed_tokens_fn(
            pipeline.tokenizer, parser
        )

        # Output and load valid JSON
        output_dict = pipeline(prompt, prefix_allowed_tokens_fn=prefix_function)
        output = output_dict[0]["generated_text"][len(prompt) :]
        json_result = json.loads(output)

        # Return valid JSON object according to the schema DeepEval supplied
        return schema(**json_result)

    async def a_generate(self, prompt: str, schema: BaseModel) -> BaseModel:
        return self.generate(prompt, schema)

    def get_model_name(self):
        return "Mistral-7B v0.3"
    



custom_model = CustomMistral7B()



answer_relevancy_metric = AnswerRelevancyMetric(model=custom_model)
context_precision = ContextualPrecisionMetric(model=custom_model)
context_recall = ContextualRecallMetric(model=custom_model)
#context_relevancy = ContextualRelevancyMetric(model=custom_model)
#hallucination = HallucinationMetric()

questions_answers = pd.read_csv("simple_evaluation_results.csv")



test_cases = []
for index, row in questions_answers.iterrows():

    test_case = LLMTestCase(
      input=row["question"],
      actual_output=row["answer"],
      retrieval_context=ast.literal_eval(row["contexts"]),
       expected_output= row["ground_truths"]
    )
    test_cases.append(test_case)

from deepeval.dataset import EvaluationDataset
dataset = EvaluationDataset(test_cases=test_cases)

dataset.evaluate([answer_relevancy_metric,context_precision,context_recall])

