#!/bin/bash

# Run the first uvicorn server
uvicorn main:app --host 127.0.0.1 --port 8000 --reload &

# Run the Streamlit app
streamlit run app.py &

# Run the second uvicorn server
uvicorn llm_simulator:app --host 0.0.0.0 --port 9090 &
