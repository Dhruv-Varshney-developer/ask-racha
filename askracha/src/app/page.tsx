"use client";

import { useState, useRef, useEffect } from "react";
import {
  Send,
  FileText,
  Loader2,
  AlertCircle,
  CheckCircle,
  Sparkles,
  Bot,
  User,
  Settings,
  Zap,
  Globe,
  ExternalLink,
} from "lucide-react";

interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  timestamp: Date;
  sources?: Array<{
    url: string;
    title: string;
    score: number;
  }>;
}

interface SystemStatus {
  initialized: boolean;
  documents_loaded: number;
  index_ready: boolean;
  query_engine_ready: boolean;
  model_info?: {
    llm: string;
    embeddings: string;
    framework: string;
  };
}
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

export default function AskRacha() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Simplified initialization process
    const initializeAndCheckStatus = async () => {
      await initializeRAG();
      await checkStatus();
    };
    initializeAndCheckStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/api/status`);
      const data = await response.json();
      setStatus(data);
      // The `isInitialized` state is now primarily driven by the backend status
      if (data.initialized || data.documents_loaded > 0 || data.vector_count > 0) {
        setIsInitialized(true);
        if (messages.length === 0) {
            addMessage(
                "assistant",
                "✨ I'm ready to help you with Storacha questions."
            );
        }
      }
    } catch (error) {
      console.error("Error checking status:", error);
    }
  };

  const initializeRAG = async () => {
    // This function now just ensures the backend is ready
    try {
      const response = await fetch(`${API_URL}/api/initialize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      const data = await response.json();
      if (!data.success) {
          addMessage("assistant", `❌ Failed to initialize: ${data.message}`);
      }
    } catch (error) {
      console.error("Error initializing RAG:", error);
       addMessage(
         "assistant",
         "❌ Error connecting to the server. Please check if the backend is running."
       );
    }
  };

  // REMOVED the `loadDefaultDocuments` function as it's no longer needed.

  const addMessage = (
    type: "user" | "assistant",
    content: string,
    sources?: any[]
  ) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      type,
      content,
      timestamp: new Date(),
      sources,
    };
    setMessages((prev) => [...prev, newMessage]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    addMessage("user", userMessage);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userMessage }),
      });

      const data = await response.json();
      if (data.success) {
        addMessage("assistant", data.answer, data.sources);
      } else {
        addMessage("assistant", `I encountered an issue: ${data.message}`);
      }
    } catch (error) {
      addMessage(
        "assistant",
        "I'm having trouble connecting to the server. Please ensure the backend is running."
      );
    }
    setIsLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const suggestions = [
    "What is Storacha and how does it work?",
    "How do I get started with the w3up client?",
    "What are the main concepts in Storacha?",
    "How do I upload files to Storacha?",
    "What are the pricing plans for Storacha?",
  ];

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Animated Background */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-purple-600/20 animate-pulse"></div>
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-bounce"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-bounce delay-1000"></div>
      </div>

      {/* Sidebar */}
      {showSidebar && (
        <div className="w-80 bg-black/40 backdrop-blur-xl border-r border-white/10 flex flex-col relative z-10">
          <div className="p-6 border-b border-white/10">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                AskRacha
              </h1>
            </div>
            <p className="text-gray-400 text-sm">
              Your AI-powered Storacha assistant
            </p>
          </div>

          <div className="flex-1 p-4 space-y-4 overflow-y-auto">
            {/* Status Card */}
            <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 border border-white/10">
              <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
                <Zap className="w-4 h-4 text-yellow-400" />
                System Status
              </h3>
              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">System</span>
                  <div className="flex items-center gap-2">
                    {isInitialized ? (
                      <CheckCircle className="h-4 w-4 text-green-400" />
                    ) : (
                      <Loader2 className="h-4 w-4 text-yellow-400 animate-spin" />
                    )}
                    <span className="text-white text-xs">
                      {isInitialized ? "Ready" : "Initializing"}
                    </span>
                  </div>
                </div>

                {status && (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-300">Documents</span>
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-blue-400" />
                        <span className="text-white text-xs">
                          {status.documents_loaded}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-300">Vector Index</span>
                      <div className="flex items-center gap-2">
                        {status.index_ready ? (
                          <CheckCircle className="h-4 w-4 text-green-400" />
                        ) : (
                          <AlertCircle className="h-4 w-4 text-gray-500" />
                        )}
                        <span className="text-white text-xs">
                          {status.index_ready ? "Ready" : "Pending"}
                        </span>
                      </div>
                    </div>
                    {status.model_info && (
                      <div className="pt-2 border-t border-white/10">
                        <div className="text-xs text-gray-400">
                          Model: {status.model_info.llm}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* Quick Actions - now shown if documents are loaded */}
            {isInitialized && (
              <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 border border-white/10">
                <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-purple-400" />
                  Quick Start
                </h3>
                <div className="space-y-2">
                  {suggestions.slice(0, 3).map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => setInput(suggestion)}
                      className="w-full text-left p-3 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-xs transition-all duration-200 border border-white/5 hover:border-white/20"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative z-10">
        {/* Header */}
        <div className="bg-black/20 backdrop-blur-xl border-b border-white/10 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {!showSidebar && (
                <button
                  onClick={() => setShowSidebar(true)}
                  className="p-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors"
                >
                  <Settings className="w-5 h-5" />
                </button>
              )}
              <div>
                <h2 className="text-xl font-semibold text-white">
                  Storacha Assistant
                </h2>
                <p className="text-sm text-gray-400">
                  {status?.documents_loaded
                    ? `Knowledge base loaded • ${status.documents_loaded} documents`
                    : "Initializing..."}
                </p>
              </div>
            </div>
            {showSidebar && (
              <button
                onClick={() => setShowSidebar(false)}
                className="p-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors"
              >
                <Settings className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center max-w-2xl">
                <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center mx-auto mb-6">
                  <Bot className="w-8 h-8 text-white" />
                </div>
                <h2 className="text-3xl font-bold text-white mb-4">
                  Welcome to AskRacha! ✨
                </h2>
                <p className="text-xl text-gray-300 mb-8">
                  Your intelligent Storacha documentation assistant powered by
                  Gemini.
                </p>
                {isInitialized && status && status.documents_loaded > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {suggestions.map((suggestion, idx) => (
                      <button
                        key={idx}
                        onClick={() => setInput(suggestion)}
                        className="p-4 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-sm transition-all duration-200 border border-white/10 hover:border-white/20 text-left"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                ) : (
                   <div className="flex items-center justify-center text-gray-400">
                     <Loader2 className="h-5 w-5 animate-spin mr-2" />
                     Initializing and loading knowledge base...
                   </div>
                )}
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.type === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-4xl rounded-2xl px-6 py-4 ${
                    message.type === "user"
                      ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg"
                      : "bg-white/10 backdrop-blur-lg border border-white/20 text-gray-100"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                        message.type === "user"
                          ? "bg-white/20"
                          : "bg-gradient-to-r from-blue-500 to-purple-500"
                      }`}
                    >
                      {message.type === "user" ? (
                        <User className="w-4 h-4" />
                      ) : (
                        <Bot className="w-4 h-4 text-white" />
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="whitespace-pre-wrap leading-relaxed">
                        {message.content}
                      </div>

                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-white/20">
                          <p className="text-sm font-medium text-gray-300 mb-2 flex items-center gap-2">
                            <ExternalLink className="w-4 h-4" />
                            Sources:
                          </p>
                          <div className="space-y-2">
                            {message.sources.map((source, idx) => (
                              <a
                                key={idx}
                                href={source.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="block p-2 rounded-lg bg-white/5 hover:bg-white/10 text-sm text-blue-300 hover:text-blue-200 transition-colors border border-white/10 hover:border-white/20"
                              >
                                {source.title}
                              </a>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl px-6 py-4 flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin text-blue-400" />
                  <span className="text-gray-300">Thinking...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-6 bg-black/20 backdrop-blur-xl border-t border-white/10">
          <form onSubmit={handleSubmit} className="flex gap-4">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  // MODIFIED placeholder text
                  isInitialized
                    ? "Ask me anything about Storacha..."
                    : "Initializing system..."
                }
                disabled={!isInitialized || isLoading}
                className="w-full px-6 py-4 bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-white/5 disabled:cursor-not-allowed text-white placeholder-gray-400 transition-all duration-200"
                rows={1}
                style={{ minHeight: "56px", maxHeight: "120px" }}
              />
            </div>
            <button
              type="submit"
              disabled={!input.trim() || !isInitialized || isLoading}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-600 disabled:to-gray-600 text-white p-4 rounded-2xl transition-all duration-200 flex items-center justify-center shadow-lg hover:shadow-xl disabled:cursor-not-allowed transform hover:scale-105 disabled:transform-none"
            >
              <Send className="h-5 w-5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}