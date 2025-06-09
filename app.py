import streamlit as st
from rag_builder import StorachaRAG

st.title("Storacha RAG Chatbot")

# Initialize session state
if 'rag' not in st.session_state:
    st.session_state.rag = StorachaRAG()
if 'index_built' not in st.session_state:
    st.session_state.index_built = False

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    # Default Storacha URLs
    default_urls = """https://docs.storacha.network/
https://github.com/storacha-network/storacha
https://github.com/storacha-network/w3up"""
    
    urls_input = st.text_area(
        "Enter URLs (one per line):",
        value=default_urls,
        height=200
    )
    
    if st.button("Build RAG Index"):
        if urls_input.strip():
            urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
            
            with st.spinner("Building index from URLs..."):
                try:
                    st.session_state.rag.build_index(urls)
                    st.session_state.index_built = True
                    st.success("Index built successfully!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.error("Please enter at least one URL")

# Main chat interface
if st.session_state.index_built:
    st.header("Ask about Storacha")
    
    question = st.text_input("Your question:")
    
    if st.button("Ask") and question:
        with st.spinner("Thinking..."):
            response = st.session_state.rag.query(question)
            st.write("**Answer:**")
            st.write(response)
else:
    st.info("Please build the RAG index first using the sidebar.")