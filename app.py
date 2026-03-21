import streamlit as st
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from rag_compliance.generation.chain import process_query_with_rag

st.set_page_config(page_title="MCA Compliance Assistant", layout="wide")

st.title("📚 MCA Compliance RAG Assistant")
st.caption("Indian Corporate Law | Companies Act 2013 | LLP Act 2008")

# Setup memory
msgs = StreamlitChatMessageHistory(key="langchain_messages")

# Setup session history function for Langchain
def get_session_history(session_id: str):
    return msgs

# Initial Greeting
if len(msgs.messages) == 0:
    msgs.add_ai_message("Hello! I am CompliCS, an AI-powered legal compliance assistant. How can I help you today?")

# Render current messages
for msg in msgs.messages:
    if msg.type == "human":
        st.chat_message("user").write(msg.content)
    else:
        st.chat_message("assistant").write(msg.content)

user_query = st.chat_input("Ask a compliance-related question...")

if user_query:
    # Render user query immediately
    st.chat_message("user").write(user_query)

    # Generate assistant response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing statutory provisions & reranking sources..."):
            stream, sources = process_query_with_rag(
                query=user_query, 
                session_id="default", 
                get_session_history_func=get_session_history
            )
            
        # Stream model output. RunnableWithMessageHistory will automatically append
        # the prompt and generated response to the 'msgs' StreamlitChatMessageHistory.
        response = st.write_stream(stream)

        # Show sources
        if sources:
            with st.expander("📄 Source References"):
                for src in sources:
                    st.markdown(f"- {src}")