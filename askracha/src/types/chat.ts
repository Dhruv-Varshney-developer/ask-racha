export interface Message {
    id: string
    type: "user" | "assistant"
    content: string
    timestamp: Date
    sources?: Array<{
        url: string
        title: string
        score: number
    }>
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
