from flask import Flask, request, jsonify
from flask_cors import CORS
from rag import AskRachaRAG
from document_scheduler import DocumentUpdateScheduler
import os
from datetime import datetime

app = Flask(__name__)
allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
CORS(app, origins=allowed_origins)

# Global RAG instance
rag = None

# Global scheduler instance
document_scheduler = None


def load_default_documents():
    """Load default documentation on server startup"""
    global rag, document_scheduler
    if not rag:
        try:
            rag = AskRachaRAG()
        except Exception as e:
            print(f"Failed to initialize RAG for default documents: {e}")
            return

    # Check if documents already exist in vector store
    try:
        stats = rag.vector_store.get_stats()
        if stats["success"] and stats["stats"].points_count > 0:
            print(
                f"Vector store already contains {stats['stats'].points_count} documents, skipping default loading"
            )
            if document_scheduler is None:
                document_scheduler = DocumentUpdateScheduler(rag)
                document_scheduler.start()
                print("Document update scheduler started")
            return
    except Exception as e:
        print(f"Could not check vector store stats: {e}")

    default_urls = [
        "https://docs.storacha.network/quickstart/",
        "https://docs.storacha.network/concepts/ucans-and-storacha/",
    ]
    
    try:
        print(f"Loading default documents on startup...")
        result = rag.load_documents(default_urls)
        if result["success"]:
            print(f"Successfully loaded {result['document_count']} default documents")
            print(rag.get_status())
            
            document_scheduler = DocumentUpdateScheduler(rag)
            document_scheduler.start()
            print("Document update scheduler started")
            
        else:
            print(f"Failed to load default documents: {result['message']}")
    except Exception as e:
        print(f"Error loading default documents: {e}")


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

@app.route('/api/load-documents', methods=['POST'])
def load_documents():
    """Load documents into the RAG system"""
    global rag
    
    if not rag:
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
        result = rag.load_documents(valid_urls)
        
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
    
    if not rag:
        return jsonify({
            'success': False,
            'message': 'RAG system not initialized. Please initialize first.'
        }), 400
    
    if not rag.query_engine:
        return jsonify({
            'success': False,
            'message': 'No documents loaded. Please load documents first.'
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
        result = rag.query(question)
        
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

@app.route("/api/vector-store/stats", methods=["GET"])
def get_vector_store_stats():
    """Get detailed information about Qdrant vector store"""
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
            from qdrant_client.http.models import ScrollRequest

            points = rag.vector_store.client.scroll(
                collection_name=rag.vector_store.collection_name,
                limit=1000,
                with_payload=True,
            )[0]

            points_info = []
            for point in points:
                point_info = {
                    "id": point.id,
                    "source": point.payload.get("source", "N/A"),
                    "title": point.payload.get("title", "N/A"),
                    "type": point.payload.get("type", "N/A"),
                    "length": point.payload.get("length", "N/A"),
                    "timestamp": point.payload.get("timestamp", "N/A"),
                    "text_preview": (
                        point.payload.get("text", "")[:100] + "..."
                        if len(point.payload.get("text", "")) > 100
                        else point.payload.get("text", "")
                    ),
                }
                points_info.append(point_info)

            return jsonify(
                {
                    "success": True,
                    "collection_name": rag.vector_store.collection_name,
                    "stats": {
                        "points_count": stats["stats"].points_count,
                        "vectors_count": stats["stats"].vectors_count,
                        "segments_count": stats["stats"].segments_count,
                        "status": stats["stats"].status,
                    },
                    # "points": points_info,
                    "total_points": len(points_info),
                }
            )

        except Exception as e:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"Failed to retrieve point details: {str(e)}",
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
    """Clear all documents from Qdrant vector store"""
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

        rag.vector_store.client.delete_collection(rag.vector_store.collection_name)
        rag.vector_store.initialize_index()

        return jsonify(
            {
                "success": True,
                "message": f"Successfully cleared vector store",
                "deleted_count": current_count,
                "collection_recreated": True,
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

    app.run(debug=False, host='0.0.0.0', port=5000)
