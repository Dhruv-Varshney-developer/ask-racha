from flask import Flask, request, jsonify
from flask_cors import CORS
from rag import AskRachaRAG
from document_scheduler import DocumentUpdateScheduler
from chat_context import ChatContextManager
from rate_limit.rate_limit_middleware import create_rate_limit_middleware
import os
import sys
from datetime import datetime
from llama_index.core import VectorStoreIndex

app = Flask(__name__)

# Enable CORS for all routes
CORS(app,
     origins='*',
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization', 'Accept', 'Origin', 'X-Chat-Context-Id'],
     supports_credentials=False)

# Initialize rate limiting middleware
rate_limit_middleware = create_rate_limit_middleware(app)

# Global RAG instance
rag = None

# Global scheduler instance
document_scheduler = None

# Global context manager instance
context_manager = ChatContextManager()

# Knowledge base loading status
kb_loading_status = {
    "status": "not_started",  # not_started, loading, ready, error
    "progress": 0,
    "message": "Knowledge base not initialized",
    "documents_loaded": 0
}


def load_default_documents():
    """Load default documentation on server startup"""
    global rag, document_scheduler, kb_loading_status
    
    kb_loading_status["status"] = "loading"
    kb_loading_status["progress"] = 10
    kb_loading_status["message"] = "Initializing RAG system..."
    
    if not rag:
        try:
            rag = AskRachaRAG()
            kb_loading_status["progress"] = 20
            kb_loading_status["message"] = "RAG system initialized"
        except Exception as e:
            print(f"Failed to initialize RAG for default documents: {e}")
            kb_loading_status["status"] = "error"
            kb_loading_status["message"] = f"Failed to initialize: {str(e)}"
            return

    # Check if documents already exist in vector store
    try:
        kb_loading_status["progress"] = 30
        kb_loading_status["message"] = "Checking existing documents..."
        
        stats = rag.vector_store.get_stats()
        if stats["success"] and stats["stats"].points_count > 0:
            print(
                f"Vector store already contains {stats['stats'].points_count} documents, skipping default loading"
            )
            kb_loading_status["progress"] = 90
            kb_loading_status["message"] = "Loading existing index..."
            kb_loading_status["documents_loaded"] = stats["stats"].points_count
            
            # Ensure scheduler is started even if we skip loading
            if document_scheduler is None:
                document_scheduler = DocumentUpdateScheduler(rag, context_manager, test_mode=False)
                document_scheduler.start()
                print("Document update scheduler started")
            
            kb_loading_status["status"] = "ready"
            kb_loading_status["progress"] = 100
            kb_loading_status["message"] = "Knowledge base ready"
            return
    except Exception as e:
        print(f"Could not check vector store stats: {e}")

    try:
        kb_loading_status["progress"] = 40
        kb_loading_status["message"] = "Processing GitHub repositories..."
        print("Processing GitHub repositories...")
        rag._process_github_repos() 
        
        kb_loading_status["progress"] = 60
        kb_loading_status["message"] = "Loading documentation..."
        
        default_urls = [
            "https://docs.storacha.network/quickstart/",
            "https://docs.storacha.network/concepts/ucans-and-storacha/",
        ]
        print(f"Loading default documents on startup...")
        result = rag.load_documents(default_urls)
        
        if result["success"]:
            kb_loading_status["progress"] = 80
            kb_loading_status["message"] = "Building search index..."
            
            print(f"🧠 Creating comprehensive index from {len(rag.documents)} documents...")
            rag.index = VectorStoreIndex.from_documents(
                rag.documents,
                show_progress=True
            )
            
            rag.query_engine = rag.index.as_query_engine(
                similarity_top_k=6,
                response_mode="tree_summarize",
                verbose=True
            )
            
            kb_loading_status["progress"] = 90
            kb_loading_status["message"] = "Starting document scheduler..."
            kb_loading_status["documents_loaded"] = len(rag.documents)
            
            print(f"Successfully loaded default documents")
            print(rag.get_status())
            
            # Initialize and start the document scheduler
            document_scheduler = DocumentUpdateScheduler(rag,context_manager)
            document_scheduler.start()
            print("Document update scheduler started")
            
            kb_loading_status["status"] = "ready"
            kb_loading_status["progress"] = 100
            kb_loading_status["message"] = "Knowledge base ready"
        else:
            print(f"Failed to load default documents: {result['message']}")
            kb_loading_status["status"] = "error"
            kb_loading_status["message"] = f"Failed to load documents: {result['message']}"
    except Exception as e:
        print(f"Error loading default documents: {e}")
        kb_loading_status["status"] = "error"
        kb_loading_status["message"] = f"Error: {str(e)}"


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

@app.route('/api/kb-status', methods=['GET'])
def get_kb_status():
    """Get knowledge base loading status"""
    global kb_loading_status
    return jsonify(kb_loading_status)
    
@app.route('/api/chat/session', methods=['POST'])
def create_chat_session():
    """Create a new chat session"""
    session_id = context_manager.create_session()
    return jsonify({
        'success': True,
        'session_id': session_id
    })

@app.route('/api/chat/query', methods=['POST'])
def chat_query():
    """Handle a chat query with context"""
    global rag
    
    if not rag:
        return jsonify({
            'success': False,
            'message': 'RAG system not initialized'
        }), 400
    
    data = request.json
    session_id = data.get('session_id')
    query = data.get('query')
    
    if not session_id or not query:
        return jsonify({
            'success': False,
            'message': 'Missing session_id or query'
        }), 400
    
    # Get session
    session = context_manager.get_session(session_id)
    if not session:
        return jsonify({
            'success': False,
            'message': 'Invalid session_id'
        }), 404
    
    context = context_manager.get_context(session_id)
    
    response = rag.query_with_context(query, context)
    
    if response['success']:
        context_manager.add_message(session_id, 'user', query)
        context_manager.add_message(
            session_id, 
            'assistant', 
            response['response'],
            {'source_nodes': response.get('source_nodes', [])}
        )
    
    return jsonify(response)

@app.route('/api/debug/sessions', methods=['GET'])
def debug_sessions():
    global context_manager

    return jsonify({
        'total_sessions': len(context_manager.sessions),
        'sessions': [{
            'id': session_id,
            'created_at': session.created_at,
            'age_seconds': (datetime.now() - datetime.fromisoformat(session.created_at)).total_seconds()
        } for session_id, session in context_manager.sessions.items()]
    })

@app.route('/api/query', methods=['POST'])
def query_documents():
    """Legacy query endpoint without context"""
    global rag
    
    if not rag:
        return jsonify({
            'success': False,
            'message': 'RAG system not initialized'
        }), 400
    
    data = request.json
    query = data.get('question')
    
    if not query:
        return jsonify({
            'success': False,
            'message': 'No question provided'
        }), 400
    
    try:
        result = rag.query(query)
        if result['success']:
            print(f"✅ Query processed successfully")
            # Add rate limit info to successful responses
            response = jsonify(result)
            
            # Add helpful rate limit information for users
            from flask import g
            if hasattr(g, 'rate_limit_result') and g.rate_limit_result:
                reset_time = g.rate_limit_result.reset_time
                response.headers['X-Next-Request-Available'] = reset_time.isoformat()
                
                # Add user-friendly message about when they can ask again
                result['rate_limit_info'] = {
                    'next_request_available': reset_time.isoformat(),
                    'message': f'You can ask your next question after {reset_time.strftime("%H:%M:%S")}'
                }
                response = jsonify(result)
            
            return response
        else:
            print(f"❌ Query failed: {result.get('answer', 'Unknown error')}")
            return jsonify({
                'success': False,
                'message': result.get('answer', 'Query processing failed'),
                'type': 'query_error'
            }), 500
        
    except Exception as e:
        print(f"❌ Error processing query: {e}")
        return jsonify({
            'success': False,
            'message': f'Error processing query: {str(e)}',
            'type': 'system_error'
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

@app.route("/api/vector-store/stats", methods=["GET"])
def get_vector_store_stats():
    """Get detailed information about Pinecone vector store"""
    global rag

    if not rag:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "RAG system not initialized. Please initialize first.",
                }
            ),
            400,
        )

    try:
        stats = rag.vector_store.get_stats()
        if not stats["success"]:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f'Failed to get vector store stats: {stats["message"]}',
                    }
                ),
                500,
            )
        
        try:
            # Get vectors from Pinecone
            vectors = rag.vector_store.get_all_vectors(limit=1000)

            vectors_info = []
            for vector_data in vectors:
                metadata = vector_data.get('metadata', {})
                vector_info = {
                    "id": vector_data.get('id', 'N/A'),
                    "source": metadata.get("source", "N/A"),
                    "title": metadata.get("title", "N/A"),
                    "type": metadata.get("type", "N/A"),
                    "length": metadata.get("length", "N/A"),
                    "timestamp": metadata.get("timestamp", "N/A"),
                    "text_preview": (
                        metadata.get("text", "")[:100] + "..."
                        if len(metadata.get("text", "")) > 100
                        else metadata.get("text", "")
                    ),
                }
                vectors_info.append(vector_info)

            return jsonify(
                {
                    "success": True,
                    "index_name": rag.vector_store.index_name,
                    "stats": {
                        "points_count": stats["stats"].points_count,
                        "vectors_count": stats["stats"].vectors_count,
                        "segments_count": stats["stats"].segments_count,
                        "status": stats["stats"].status,
                    },
                    "total_vectors": len(vectors_info),
                }
            )

        except Exception as e:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"Failed to retrieve vector details: {str(e)}",
                    }
                ),
                500,
            )

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Error getting vector store stats: {str(e)}",
                }
            ),
            500,
        )

@app.route("/api/vector-store/clear", methods=["POST"])
def clear_vector_store():
    """Clear all documents from Pinecone vector store"""
    if os.getenv('FLASK_ENV') == 'production':
        return jsonify({
            'success': False,
            'message': 'This endpoint is disabled in production for data safety'
        }), 403
    
    global rag

    if not rag:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "RAG system not initialized. Please initialize first.",
                }
            ),
            400,
        )

    try:
        stats = rag.vector_store.get_stats()
        if not stats["success"]:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f'Failed to get current stats: {stats["message"]}',
                    }
                ),
                500,
            )

        current_count = stats["stats"].points_count

        if current_count == 0:
            return jsonify(
                {
                    "success": True,
                    "message": "Vector store is already empty",
                    "deleted_count": 0,
                }
            )

        # Delete all vectors from Pinecone index
        rag.vector_store.index.delete(delete_all=True)

        return jsonify(
            {
                "success": True,
                "message": f"Successfully cleared vector store",
                "deleted_count": current_count,
                "index_cleared": True,
            }
        )

    except Exception as e:
        return (
            jsonify(
                {"success": False, "message": f"Error clearing vector store: {str(e)}"}
            ),
            500,
        )


@app.route("/api/scheduler/status", methods=["GET"])
def get_scheduler_status():
    """Get document scheduler status"""
    global document_scheduler
    
    if not document_scheduler:
        return jsonify({
            'success': False,
            'message': 'Document scheduler not initialized'
        }), 400
    
    try:
        status = document_scheduler.get_status()
        return jsonify({
            'success': True,
            'scheduler_status': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting scheduler status: {str(e)}'
        }), 500


@app.route("/api/scheduler/trigger-update", methods=["POST"])
def trigger_manual_update():
    """Manually trigger document update"""
    global document_scheduler
    
    if not document_scheduler:
        return jsonify({
            'success': False,
            'message': 'Document scheduler not initialized'
        }), 400
    
    try:
        result = document_scheduler.trigger_manual_update()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error triggering manual update: {str(e)}'
        }), 500


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print("🚀 Version 2")
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
    
    load_default_documents()

    app.run(debug=True, host='0.0.0.0', port=5000)
