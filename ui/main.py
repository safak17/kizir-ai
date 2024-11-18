# main.py
from fastapi import FastAPI, WebSocket
import websockets
import asyncio

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    uri = "ws://localhost:9090/llm"  # LLM taklit edicinin portu
    await websocket.accept()
    try:
        async with websockets.connect(uri) as llm_websocket:
            while True:
                data = await websocket.receive_text()
                await llm_websocket.send(data)

                # LLM'den gelen her kelimeyi client'a iletin
                while True:
                    response = await llm_websocket.recv()
                    if "<end-of-response>" in response:
                        break
                    await websocket.send_text(response)
    except websockets.exceptions.ConnectionClosedError:
        await websocket.close()
        return "Connection was closed unexpectedly."
