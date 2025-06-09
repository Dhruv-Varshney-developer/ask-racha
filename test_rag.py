from rag_builder import StorachaRAG

# Test URLs
urls = [
    "https://docs.storacha.network/",
    "https://github.com/storacha-network/storacha",
    "https://github.com/storacha-network/w3up"
]

# Build and test
rag = StorachaRAG()
print("Building index...")
rag.build_index(urls)

print("Testing query...")
response = rag.query("What is Storacha?")
print(f"Response: {response}")