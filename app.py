import streamlit as st
from ultra_simple_rag import UltraSimpleRAG

st.set_page_config(page_title="Storacha RAG", page_icon="📚")

st.title("📚 Storacha RAG Chatbot")
st.markdown("*Ask questions about Storacha documentation*")

# Initialize session state
if 'rag' not in st.session_state:
    st.session_state.rag = UltraSimpleRAG()
if 'loaded' not in st.session_state:
    st.session_state.loaded = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Sidebar for setup
with st.sidebar:
    st.header("🔧 Setup")
    
    # API Key check
    if not st.session_state.rag.openai_api_key:
        st.error("⚠️ OpenAI API key not found in .env file")
        st.stop()
    else:
        st.success("✅ OpenAI API key loaded")
    
    # URL input
    st.subheader("📄 Documents to Load")
    default_urls = """https://docs.storacha.network/
    https://storacha.network/
    https://docs.storacha.network/quickstart/
    https://docs.storacha.network/concepts/
    https://docs.storacha.network/how-tos/"""
    
    urls_input = st.text_area(
        "URLs (one per line):",
        value=default_urls,
        height=120,
        help="Enter documentation URLs to scrape and index"
    )
    
    if st.button("🔄 Load Documents", type="primary"):
        if urls_input.strip():
            urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
            
            with st.spinner("Loading documents..."):
                progress_bar = st.progress(0)
                st.session_state.rag.load_documents(urls)
                progress_bar.progress(100)
                
                if st.session_state.rag.documents:
                    st.session_state.loaded = True
                    st.success(f"✅ Loaded {len(st.session_state.rag.documents)} documents!")
                    
                    # Show preview
                    st.subheader("📋 Loaded Documents")
                    for doc in st.session_state.rag.documents:
                        st.write(f"🔗 **{doc['source']}**")
                        st.write(f"📄 {doc['preview']}")
                        st.write("---")
                else:
                    st.error("❌ No documents could be loaded")
        else:
            st.error("Please enter at least one URL")
    
    if st.session_state.loaded:
        st.write(f"📚 **{len(st.session_state.rag.documents)} documents ready**")

# Main chat interface
if st.session_state.loaded:
    st.header("💬 Chat")
    
    # Display chat history
    for i, (question, answer) in enumerate(st.session_state.chat_history):
        with st.container():
            st.write(f"**🤔 You:** {question}")
            st.write(f"**🤖 Bot:** {answer}")
            st.write("---")
    
    # Question input
    with st.form("question_form"):
        question = st.text_input(
            "Ask a question about Storacha:",
            placeholder="e.g., What is Storacha? How do I get started?"
        )
        submitted = st.form_submit_button("Ask", type="primary")
        
        if submitted and question:
            with st.spinner("🤔 Thinking..."):
                answer = st.session_state.rag.query(question)
                
                # Add to history
                st.session_state.chat_history.append((question, answer))
                
                # Display new answer
                st.write(f"**🤔 You:** {question}")
                st.write(f"**🤖 Bot:** {answer}")
                
                # Auto-scroll by rerunning
                st.rerun()

else:
    st.info("👈 Please load documents first using the sidebar")
    st.markdown("### 🚀 Getting Started")
    st.markdown("""
    1. Make sure your `.env` file contains your OpenAI API key
    2. Use the sidebar to add documentation URLs
    3. Click "Load Documents" to scrape and index the content
    4. Start asking questions!
    """)