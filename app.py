import streamlit as st


# ---------------- MOCK RAG FUNCTION ----------------
def ask_rag(query, top_k):
    answer = (
        "Under the Companies Act, 2013, every company is required to file "
        "its annual financial statements with the Registrar of Companies "
        "within 30 days of the Annual General Meeting (AGM)."
    )

    sources = [
        {
            "title": "Companies Act, 2013 – Section 137",
            "content": "A copy of the financial statements shall be filed with the Registrar..."
        },
        {
            "title": "Companies Act, 2013 – Section 92",
            "content": "Every company shall file its annual return within sixty days..."
        }
    ][:top_k]

    return answer, sources


# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Corporate Compliance RAG Assistant",
    page_icon="📘",
    layout="wide"
)


# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("⚙️ Settings")

    top_k = st.slider(
        "Number of documents to retrieve",
        min_value=1,
        max_value=10,
        value=5
    )

    show_debug = st.checkbox("Show debug info")


# ---------------- MAIN UI ----------------
st.title("📘 Corporate Compliance RAG Assistant")

question = st.text_input(
    "Ask a compliance question",
    placeholder="What are the annual ROC filing requirements?"
)

if st.button("Ask"):
    if question.strip():
        with st.spinner("Processing..."):
            answer, sources = ask_rag(question, top_k)

        st.subheader("🧠 Answer")
        st.success(answer)

        st.subheader("📚 Sources")
        for src in sources:
            with st.expander(src["title"]):
                st.write(src["content"])

        if show_debug:
            st.subheader("🔍 Debug")
            st.write("Retrieved", len(sources), "documents")
    else:
        st.warning("Please enter a question")
