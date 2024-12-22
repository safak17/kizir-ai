# llm_simulator.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import pandas as pd
import json
import asyncio
from rag_simple import CourseRecommendationAssistant


app = FastAPI()

assistant = CourseRecommendationAssistant(
    model_path="models/gemma-2-9b-it-Q8_0.gguf",
    embedding_model_name="sentence-transformers/all-MiniLM-L6-v2",
    vectorstore_path="faiss_index_regulations_added",
    callback_use=False,
    topk=15
)




@app.websocket("/llm")
async def llm_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            
            data_json = await websocket.receive_text()
            try:
                parsed_data = json.loads(data_json)
            except Exception as e:
                logging.error(f"Error: {e}")
                break
            session_id = parsed_data.get("session_id")
            data = parsed_data.get("message")
            question_summarized,response = await assistant.stream(data,session_id)
            total_response = ""
            async for word in response:
                total_response += word
                await websocket.send_text(word)
            await assistant.add_to_chat_history(session_id,total_response,question_summarized)
            await websocket.send_text("<end-of-response>")  
    except WebSocketDisconnect:
        print("Client disconnected gracefully.")
