from langchain_community.llms import LlamaCpp
from langchain_community.llms import Ollama
#from langchain_ollama import ChatOllama
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler
from langchain_core.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.callbacks import get_openai_callback
from langchain_openai import OpenAI
import os 
import time
from transformers import AutoTokenizer

class CourseRecommendationAssistant:
    def __init__(self, model_path, embedding_model_name, vectorstore_path = None,callback_use = True,topk=5,template_version=1,device="cpu"):
        # Define the system prompts
        if template_version == 1:
            self.template = """SYSTEM MESSAGE:
    You are an AI assistant at Middle East Technical University that recommends courses and give information about regulations. You politely listen and respond to prospective students or students questions about courses and regulations. You were asked your first question by the student. STUDENT USER: {question} 
    
    Answer the question if it's related to the courses and remind your objective if it is not related to courses and regulations. Use the documents below to answer the question {docs} . You have all the information that you need to answer the question. You will recommend courses with their names and course codes. If course has any prerequisite, then specify it as well. Recommend courses everytime if any course related question is asked. If a graduate program related question is asked, give a general information about that program and answer the question. If the question is unrelated to courses and regulations, do not recommend courses. Use the documents as course catalog.
    SYSTEM ANSWER: """
        if template_version == 0:
            self.template = """SYSTEM MESSAGE:
    You are an AI assistant at Middle East Technical University that recommends courses and give information about regulations. You take the question {question}. Answer the question if it's related to topic. Use documents {docs} to answer.
    SYSTEM ANSWER: """
            
            

        self.summarize_template = """You are an AI assistant at Middle East Technical University that recommends courses and give information about regulations. You have taken chat history '{chat_history}' and input question '{question}'. Summarize the input question using the chat history as a one sentence output. If no chat history found then only use the given input question.
SUMMARIZED ANSWER:  """

        self.topk = topk 
        if embedding_model_name == "sentence-transformers/all-MiniLM-L6-v2":
            vectorstore_path = "faiss_index_regulations_added"
        if embedding_model_name == "TaylorAI/gte-tiny":
            vectorstore_path = "faiss_index_regulations_added_gte"
            
        # Initialize prompts
        self.prompt = PromptTemplate.from_template(self.template)
        self.summarize_prompt = PromptTemplate.from_template(self.summarize_template)

        
        # Callback manager for streaming outputs
        if callback_use:
            self.callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
        else:
            self.callback_manager = None
            

        # LLM model configuration
        self.llm =  OpenAI(openai_api_base=os.environ.get("LLAMACPP_API_ENDPOINT", "http://localhost:8070/v1"), openai_api_key="hello.world")
        #self.llm = LlamaCpp(
        #    model_path=model_path,
        #    n_gpu_layers=-1,
        #    n_batch=512,
        #    max_tokens = 8192,
        #    n_ctx=8192,
        #    callback_manager=self.callback_manager,
        #    verbose=False,
        #)
        self.llm = Ollama(model="gemma2:9b-instruct-q8_0",num_ctx=8192)
        #self.llm = ChatOllama(model="gemma2:9b-instruct-q8_0")
        tokenizer_path = "google/gemma-2-2b"  

        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        # Embedding model configuration
        model_kwargs = {'device': device}
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name, model_kwargs=model_kwargs)

        # Load vector store
        self.vectorstore = FAISS.load_local(vectorstore_path, self.embeddings, allow_dangerous_deserialization=True)

        # Set up chains for prompt and summarization
        self.llm_chain = self.prompt | self.llm
        self.summarize_chain = self.summarize_prompt | self.llm

        self.session_histories = {}
        #self.chat_history = []

    def initialize_session(self, session_id):
        """Initialize session history for a new session_id."""
        if session_id not in self.session_histories:
            self.session_histories[session_id] = []

    async def add_to_chat_history(self, session_id, response, question_summarized):
        """Adds messages to the session-specific chat history."""
        self.initialize_session(session_id)
        self.session_histories[session_id].extend([
            HumanMessage(content=question_summarized),
            AIMessage(content=response),
        ])

    def delete_session_history(self, session_id):
        """Deletes the chat history for a specific session_id."""
        if session_id in self.session_histories:
            del self.session_histories[session_id]
            print(f"Deleted session history for session: {session_id}")

    async def get_summary(self, question, chat_history,session_id):
        self.initialize_session(session_id)
        """Summarizes the question based on chat history."""
        return await self.summarize_chain.ainvoke({"question": question, "chat_history": chat_history})

    def reset_history(self):
        self.chat_history = []
        

    def retrieve_documents(self, question_summarized):
        """Retrieves the top k similar documents for a given question."""
        return self.vectorstore.similarity_search(question_summarized, k=self.topk)

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
        self.reset_history()
        return response,docs

    async def stream(self,question,session_id):
        self.initialize_session(session_id)
        chat_history = self.session_histories[session_id]
        print("Question",question)
        #question_summarized = self.summarize_chain.astream({"question": question, "chat_history": self.chat_history})
        question_summarized = await self.get_summary(question, chat_history,session_id)
        print("Summarized Question",question_summarized)
        docs = self.retrieve_documents(question_summarized)
        print("Summarized Question",question_summarized)
        print(docs)
        response = self.llm_chain.astream({"question": question_summarized, "docs": docs})
        return question_summarized,response



# Initialize and run the assistant
"""
assistant = CourseRecommendationAssistant(
    model_path="models/gemma-2-9b-it-Q8_0.gguf",
    embedding_model_name="sentence-transformers/all-MiniLM-L6-v2",
    vectorstore_path="faiss_index"
)
"""

#assistant.interact()
