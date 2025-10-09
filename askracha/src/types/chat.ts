export interface ChatSession {
    session_id: string;
    created_at: string;
    last_active: string;
}

export interface Message {
    id: string;
    type: "user" | "assistant";
    content: string;
    timestamp: Date;
    sources?: Array<{
        url: string;
        title: string;
        score: number;
    }>;
    metadata?: Record<string, any>;
}

export interface SystemStatus {
    initialized: boolean
    documents_loaded: number
    index_ready: boolean
    query_engine_ready: boolean
    model_info?: {
        llm: string
        embeddings: string
        framework: string
    }
}
