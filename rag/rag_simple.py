from langchain_community.llms import LlamaCpp
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler
from langchain_core.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.callbacks import get_openai_callback
import time
from transformers import AutoTokenizer

class CourseRecommendationAssistant:
    def __init__(self, model_path, embedding_model_name, vectorstore_path):
        # Define the system prompts
        self.template = """SYSTEM MESSAGE:
You are an AI assistant at Middle East Technical University that recommends courses and give information about regulations. You politely listen and respond to prospective students or students questions about courses and regulations. Ask questions and try to better narrow down what student want to do.You were just asked your first question by the student. STUDENT USER: {question} 

Answer the question if it's related to the courses and remind your objective if it is not related to courses and regulations. Use the documents below to answer the question {docs} . Recommend courses if suitable.
SYSTEM ANSWER: """

        self.summarize_template = """You are an AI assistant at Middle East Technical University that recommends courses and give information about regulations. You have taken chat history '{chat_history}' and input question '{question}'. Summarize the input question using the chat history as a one sentence output. """

        # Initialize prompts
        self.prompt = PromptTemplate.from_template(self.template)
        self.summarize_prompt = PromptTemplate.from_template(self.summarize_template)


        # Callback manager for streaming outputs
        self.callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

        # LLM model configuration
        self.llm = LlamaCpp(
            model_path=model_path,
            n_gpu_layers=-1,
            n_batch=512,
            n_ctx=8192,
            callback_manager=self.callback_manager,
            verbose=False,
        )

        tokenizer_path = "google/gemma-2-2b"  

        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        # Embedding model configuration
        model_kwargs = {'device': 'cuda:0'}
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name, model_kwargs=model_kwargs)

        # Load vector store
        self.vectorstore = FAISS.load_local(vectorstore_path, self.embeddings, allow_dangerous_deserialization=True)

        # Set up chains for prompt and summarization
        self.llm_chain = self.prompt | self.llm
        self.summarize_chain = self.summarize_prompt | self.llm

        self.chat_history = []

    def get_summary(self, question, chat_history):
        """Summarizes the question based on chat history."""
        return self.summarize_chain.invoke({"question": question, "chat_history": chat_history})

    def reset_history(self):
        self.chat_history = []
        

    def retrieve_documents(self, question_summarized, k=5):
        """Retrieves the top k similar documents for a given question."""
        return self.vectorstore.similarity_search(question_summarized, k=k)

    def get_response(self, question, docs):
        """Generates a response using the question and retrieved documents."""
        return self.llm_chain.invoke({"question": question, "docs": docs})


    def interact(self,debug=False):
        """Main interaction loop for the assistant."""
        print("Welcome to the course recommendation assistant! Type 'exit' to end the conversation.\n")
        chat_history = []

        while True:
            question = input("You: ")
            if question.lower() == "exit":
                print("Exiting the assistant. Have a great day!")
                break

            # Summarize the question
            question_summarized = self.get_summary(question, chat_history)

            # Fetch relevant documents
            docs = self.retrieve_documents(question_summarized)
            if debug:
                print(docs)
            # Get the response
            response = self.get_response(question, docs)

            # Append to chat history
            chat_history.extend([
                HumanMessage(content=question_summarized),
                AIMessage(content=response),
            ])

    def forward(self,question):
        
        question_summarized = self.get_summary(question, self.chat_history)

        # Fetch relevant documents
        docs = self.retrieve_documents(question_summarized)


        # Get the response
        response = self.get_response(question, docs)

        # Append to chat history
        self.chat_history.extend([
            HumanMessage(content=question_summarized),
            AIMessage(content=response),
        ])
        return response

    def performance_metrics(self,question):

        start_time = time.time()
        question_summarized = self.get_summary(question, self.chat_history)

        # Fetch relevant documents
        docs = self.retrieve_documents(question_summarized)


        # Get the response
        
        response= self.get_response(question, docs)
        
        # Append to chat history
        self.chat_history.extend([
            HumanMessage(content=question_summarized),
            AIMessage(content=response),
        ])
        end_time = time.time()
        latency = end_time - start_time
        print("Latency of the model", latency)
        num_tokens = len(self.tokenizer.encode(response))
        tokens_per_sec = num_tokens / latency
        return response,tokens_per_sec
    
    def evaluate(self,question):
        
        question_summarized = self.get_summary(question, self.chat_history)

        # Fetch relevant documents
        docs = self.retrieve_documents(question_summarized)


        # Get the response
        response = self.get_response(question, docs)

        # Append to chat history
        self.chat_history.extend([
            HumanMessage(content=question_summarized),
            AIMessage(content=response),
        ])
        return response,docs




# Initialize and run the assistant
"""
assistant = CourseRecommendationAssistant(
    model_path="models/gemma-2-9b-it-Q8_0.gguf",
    embedding_model_name="sentence-transformers/all-MiniLM-L6-v2",
    vectorstore_path="faiss_index"
)
"""

#assistant.interact()
