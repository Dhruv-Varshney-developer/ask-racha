from flask import Flask, render_template, request, jsonify
from rag import StorachaRAG
import os

app = Flask(__name__)
rag = StorachaRAG()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/load_documents', methods=['POST'])
def load_documents():
    urls = request.json.get('urls', [])
    try:
        rag.load_documents(urls)
        return jsonify({
            'success': True, 
            'message': f'Loaded {len(rag.documents)} documents',
            'documents': [{'source': doc['source'], 'preview': doc['preview']} for doc in rag.documents]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/query', methods=['POST'])
def query():
    question = request.json.get('question', '')
    try:
        answer = rag.query(question)
        return jsonify({'success': True, 'answer': answer})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)