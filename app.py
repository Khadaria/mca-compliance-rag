import streamlit as st
from llm import generate_answer

st.set_page_config(page_title="MCA Compliance Assistant", layout="wide")

st.title("📚 MCA Compliance RAG Assistant")

st.caption("Indian Corporate Law | Companies Act 2013 | LLP Act 2008")

# -------------------------------
# Session Memory
# -------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------------
# Display Chat History
# -------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -------------------------------
# Chat Input
# -------------------------------
user_query = st.chat_input("Ask a compliance-related question...")

if user_query:

    # Show user message
    st.session_state.messages.append(
        {"role": "user", "content": user_query}
    )

    with st.chat_message("user"):
        st.markdown(user_query)

    # Generate assistant response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing statutory provisions..."):
            answer, sources = generate_answer(user_query)

        st.markdown(answer)

        if sources:
            with st.expander("📄 Source References"):
                for src in sources:
                    st.markdown(f"- {src}")

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )
