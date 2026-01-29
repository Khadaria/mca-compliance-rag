import streamlit as st

# ---- PAGE CONFIG ----
st.set_page_config(page_title="Compliance RAG Assistant", layout="wide")

st.title("📘 Corporate Compliance RAG Assistant (India)")
st.caption("Companies Act, 2013 & LLP Act, 2008")

# ---- INPUT ----
question = st.text_input(
    "Ask a compliance question",
    placeholder="What are the annual ROC filing requirements?"
)

# ---- BUTTON ----
if st.button("Ask"):
    if question.strip() == "":
        st.warning("Please enter a question")
    else:
        with st.spinner("Searching compliance documents..."):
            answer, sources = ask_rag(question)

        st.subheader("🧠 Answer")
        st.write(answer)

        st.subheader("📚 Sources")
        for s in sources:
            with st.expander(s["title"]):
                st.write(s["content"])

def ask_rag(query):
    answer = (
        "As per the Companies Act, 2013, every company is required "
        "to file its annual financial statements with the Registrar "
        "of Companies within 30 days of the AGM."
    )

    sources = [
        {
            "title": "Companies Act, 2013 – Section 137",
            "content": "A copy of the financial statements shall be filed with the Registrar..."
        }
    ]

    return answer, sources
