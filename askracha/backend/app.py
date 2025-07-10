from flask import Flask, request, jsonify
from flask_cors import CORS
from rag import AskRachaRAG
import os
from datetime import datetime

app = Flask(__name__)
allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
CORS(app, origins=allowed_origins)

# Global RAG instance
rag = None

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'AskRacha RAG API',
        'version': '2.0'
    })

@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    """Test Gemini API connection"""
    global rag
    
    if not rag:
        try:
            rag = AskRachaRAG()
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Failed to initialize RAG: {str(e)}'
            }), 500
    
    result = rag.test_connection()
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

@app.route('/api/initialize', methods=['POST'])
def initialize_rag():
    """Initialize the RAG system"""
    global rag
    try:
        print("🚀 Initializing AskRacha RAG system...")
        rag = AskRachaRAG()
        # Internally it will hydrate from Pinecone via from_vector_store()
        if not rag.index:
            return jsonify({
                'success': False,
                'message': 'Index hydration failed no existing vectors found.'
            }), 500
        
        # Test the connection
        test_result = rag.test_connection()
        if not test_result['success']:
            return jsonify({
                'success': False,
                'message': f'RAG initialized but API test failed: {test_result["message"]}'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'RAG system initialized successfully with Gemini 2.0 Flash',
            'status': rag.get_status(),
            'api_test': test_result
        })
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to initialize RAG system: {str(e)}'
        }), 500

@app.route('/api/load-documents', methods=['POST'])
def load_documents():
    """Load documents into the RAG system"""
    global rag
    
    if not rag or not rag.index:
        return jsonify({
            'success': False,
            'message': 'RAG system not initialized. Please initialize first.'
        }), 400
    
    data = request.get_json()
    urls = data.get('urls', [])
    
    if not urls:
        return jsonify({
            'success': False,
            'message': 'No URLs provided'
        }), 400
    
    # Validate URLs
    valid_urls = []
    for url in urls:
        url = url.strip()
        if url and (url.startswith('http://') or url.startswith('https://')):
            valid_urls.append(url)
    
    if not valid_urls:
        return jsonify({
            'success': False,
            'message': 'No valid URLs provided'
        }), 400
    
    try:
        print(f"📄 Loading {len(valid_urls)} documents...")
        result = rag.build_index_from_urls(valid_urls)
        
        if result['success']:
            print(f"✅ Successfully loaded {result['document_count']} documents")
        else:
            print(f"❌ Failed to load documents: {result['message']}")
        
        return jsonify(result)
    except Exception as e:
        print(f"❌ Error loading documents: {e}")
        return jsonify({
            'success': False,
            'message': f'Error loading documents: {str(e)}'
        }), 500

@app.route('/api/query', methods=['POST'])
def query_documents():
    """Query the RAG system"""
    global rag
    
    if not rag or not rag.query_engine:
        return jsonify({
            'success': False,
            'message': 'RAG not ready – initialize and load documents first.'
        }), 400
    
    data = request.get_json()
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({
            'success': False,
            'message': 'No question provided'
        }), 400
    
    try:
        print(f"🤔 Processing query: {question[:100]}...")
        result = rag.query_sync(question)
        
        if result['success']:
            print(f"✅ Query processed successfully")
        else:
            print(f"❌ Query failed: {result.get('answer', 'Unknown error')}")
        
        return jsonify(result)
    except Exception as e:
        print(f"❌ Error processing query: {e}")
        return jsonify({
            'success': False,
            'message': f'Error processing query: {str(e)}'
        }), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get RAG system status"""
    global rag
    
    if not rag:
        return jsonify({
            'initialized': False,
            'message': 'RAG system not initialized'
        })
    
    try:
        status = rag.get_status()
        status['initialized'] = True
        return jsonify(status)
    except Exception as e:
        return jsonify({
            'initialized': False,
            'message': f'Error getting status: {str(e)}'
        }), 500

@app.route('/api/reset', methods=['POST'])
def reset_system():
    """Reset the RAG system"""
    global rag
    try:
        rag = None
        return jsonify({
            'success': True,
            'message': 'RAG system reset successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error resetting system: {str(e)}'
        }), 500

@app.route('/api/documents', methods=['GET'])
def list_documents():
    """List loaded documents"""
    global rag
    
    if not rag or not rag.documents:
        return jsonify({
            'documents': [],
            'count': 0
        })
    
    try:
        documents_info = []
        for doc in rag.documents:
            doc_info = {
                'source': doc.metadata.get('source', 'Unknown'),
                'title': doc.metadata.get('title', 'Untitled'),
                'length': doc.metadata.get('length', 0),
                'type': doc.metadata.get('type', 'unknown'),
                'preview': doc.text[:200] + "..." if len(doc.text) > 200 else doc.text
            }
            documents_info.append(doc_info)
        
        return jsonify({
            'documents': documents_info,
            'count': len(documents_info)
        })
    except Exception as e:
        return jsonify({
            'error': f'Error listing documents: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("🚀 Starting AskRacha API Server...")
    print("📡 API available at: http://localhost:5000")
    print("🔗 Accepting requests from: http://localhost:3000")
    print("📚 Using Gemini 2.0 Flash + LlamaIndex")
    
    # Check for API key on startup
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  WARNING: GEMINI_API_KEY not found in environment!")
        print("   Please set your API key in backend/.env")
    else:
        print("✅ Gemini API key detected")
    
    app.run(debug=True, host='0.0.0.0', port=5000)