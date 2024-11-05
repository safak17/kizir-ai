from fastapi import FastAPI, WebSocket
from typing import List
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

async def generate_response(message: str) -> str:
    # Burada yanıtı oluşturmak için bir model (örneğin OpenAI API) çağırabilirsin.
    # Örnek olarak sabit bir yanıt döndüreceğiz.
    return f"dummy message: {message}"  # Basitçe mesajı ters çevirerek döndür

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        response = await generate_response(data)
        await websocket.send_text(response)
