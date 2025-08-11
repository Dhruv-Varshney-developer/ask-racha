import json
from flask import Flask, request, jsonify, make_response
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
    global rag
    try:
        # 1) Instantiate once
        if rag is None:
            rag = AskRachaRAG()
        
        # 2) Ensure existing index
        if not rag.index:
            return jsonify({
                'success': False,
                'message': 'Index hydration failed: no existing vectors found.'
            }), 500

        # 3) Test Gemini connectivity
        test_result = rag.test_connection()
        safe_test = json.loads(json.dumps(test_result))
        if not test_result.get('success'):
            return jsonify({
                'success': False,
                'message': f'API test failed: {test_result.get("message")}'
            }), 500

        # 4) Fetch system status
        status_payload = rag.get_status()
        safe_payload = json.loads(json.dumps(status_payload))
        if not status_payload.get('success'):
            return jsonify({
                'success': False,
                'message': f'Status check failed: {status_payload.get("message")}'
            }), 500

        # 5) All good: send back success + status + api_test
        return jsonify({
            'success': True,
            'message': 'RAG system initialized successfully with Gemini 2.0 Flash',
            'status': safe_payload,
            'api_test': safe_test
        })

    except Exception as e:
        app.logger.exception("Initialization error")
        return jsonify({
            'success': False,
            'message': f'Failed to initialize RAG system: {e}'
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
    global rag
    try:
        if rag is None:
            return jsonify({
                'success': False,
                'initialized': False,
                'message': 'RAG system not initialized'
            }), 200

        status_payload = rag.get_status()
        safe_payload = json.loads(json.dumps(status_payload))
        # Ensure payload has success flag
        if not status_payload.get('success', True):
            return jsonify({
                'success': False,
                'initialized': False,
                'message': safe_payload.get('message', 'Unknown status error')
            }), 500

        status_payload['initialized'] = True
        return jsonify(safe_payload), 200

    except Exception as e:
        app.logger.exception("Status retrieval error")
        return jsonify({
            'success': False,
            'initialized': False,
            'message': f'Error getting status: {e}'
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
    
    app.run(debug=True, host='127.0.0.1', port=5000)
