from __future__ import annotations

import os

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
DEFAULT_SESSION_ID = os.getenv("CHAT_SESSION_ID", "demo-session")

st.set_page_config(page_title="Zoho Agent Chat", page_icon="🤖", layout="centered")

st.title("Zoho Creator Agent")
st.caption("Ask questions in natural language")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

question = st.chat_input("Ask a question")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/chat",
                    json={
                        "question": question,
                        "session_id": DEFAULT_SESSION_ID,
                        "max_rows": 20,
                    },
                    timeout=120,
                )
                response.raise_for_status()
                data = response.json()
                answer = data.get("summary", "No answer generated.")
            except Exception as exc:  # pragma: no cover
                answer = f"Error: {exc}"

        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
