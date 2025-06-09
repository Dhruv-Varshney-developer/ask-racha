from rag import StorachaRAG

# Test with minimal URLs
urls = [
    "https://storacha.network/",
    "https://docs.storacha.network/"
]

print("Creating RAG system...")
rag = StorachaRAG()

print("Loading documents...")
rag.load_documents(urls)

if rag.documents:
    print(f"\nLoaded {len(rag.documents)} documents")
    
    print("\nTesting query...")
    response = rag.query("What is Storacha?")
    print(f"\nResponse:\n{response}")
else:
    print("No documents loaded!")