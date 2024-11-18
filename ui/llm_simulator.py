# llm_simulator.py
from fastapi import FastAPI, WebSocket
import asyncio

app = FastAPI()

async def generate_response_stream(message: str):
    words = message.split()
    for word in words:
        yield word + " "  # Kelimeyi gönder ve aralarına boşluk ekle
        await asyncio.sleep(0.3)  # Her kelime için bekleme süresi (taklit amaçlı)

@app.websocket("/llm")
async def llm_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        async for word in generate_response_stream(data):
            await websocket.send_text(word)
        await websocket.send_text("<end-of-response>")  # Bitiş sinyali
