# llm_simulator.py
from fastapi import FastAPI, WebSocket
import asyncio
import json
import logging

app = FastAPI()
# Configure logging to output to the terminal
logging.basicConfig(
    level=logging.CRITICAL,  # Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Log messages to the terminal
    ]
)
async def generate_response_stream(message: str):
    words = message.split()
    for word in words:
        yield word + " "  # Kelimeyi gönder ve aralarına boşluk ekle
        await asyncio.sleep(0.3)  # Her kelime için bekleme süresi (taklit amaçlı)

@app.websocket("/llm")
async def llm_endpoint(websocket: WebSocket):
    logging.debug(f"LLM HAS INPUT")

    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            try:
                parsed_data = json.loads(data)
            except Exception as e:
                logging.error(f"Error: {e}")
                break
            
            # Log parsed session_id and message
            logging.info(f"LLM: {parsed_data}")

            # Extract session_id and message
            session_id = parsed_data.get("session_id")
            message = parsed_data.get("message")

            async for word in generate_response_stream(message):
                # Log each word being sent
                await websocket.send_text({word})
                logging.info(f"{word}")
            await websocket.send_text("<end-of-response>")  # End signal
        except Exception as e:
            logging.error(f"Error: {e}")
            break