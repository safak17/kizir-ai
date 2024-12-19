@echo off
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
streamlit run app.py
uvicorn llm_simulator:app --host 0.0.0.0 --port 9090