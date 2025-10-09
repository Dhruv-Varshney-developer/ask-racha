"use client"

import type React from "react"
import { useState, useCallback, useEffect, useRef } from "react"
import { useRouter, useParams } from 'next/navigation'
import type { Message } from "@/types/chat"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"

export function useChat({ initialSessionId }: { initialSessionId?: string } = {}) {
    const router = useRouter();
    const params = useParams();
    
    const [sessionId, setSessionId] = useState<string>(() => {
        if (initialSessionId) return initialSessionId;
        if (params?.session_id) return params.session_id as string;
        if (typeof window !== "undefined") {
            return localStorage.getItem("askracha-session-id") || "";
        }
        return "";
    });

    const [messages, setMessages] = useState<Message[]>(() => {
        if (typeof window !== "undefined") {
            const saved = localStorage.getItem(`askracha-messages-${sessionId}`)
            return saved ? JSON.parse(saved) : []
        }
        return []
    })

    const [input, setInput] = useState("")
    const [isLoading, setIsLoading] = useState(false)

    useEffect(() => {
        const initSession = async () => {
            if (!sessionId) {
                try {
                    const response = await fetch(`${API_URL}/api/chat/session`, {
                        method: "POST"
                    });
                    const data = await response.json();
                    if (data.success) {
                        const newSessionId = data.session_id;
                        setSessionId(newSessionId);
                        
                        localStorage.setItem("askracha-session-id", newSessionId);
                        document.cookie = `askracha-session-id=${newSessionId}; path=/; max-age=2592000`; // 30 days
                        
                        router.push(`/chat/${newSessionId}`);
                    }
                } catch (error) {
                    console.error("Failed to initialize chat session:", error);
                }
            }
        };

        initSession();
    }, [sessionId, router]);

    useEffect(() => {
        if (params?.session_id && params.session_id !== sessionId) {
            setSessionId(params.session_id as string);
            localStorage.setItem("askracha-session-id", params.session_id as string);
        }
    }, [params?.session_id]);

    // Save messages to localStorage whenever they change
    const saveMessages = useCallback((newMessages: Message[]) => {
        setMessages(newMessages)
        if (typeof window !== "undefined" && sessionId) {
            localStorage.setItem(`askracha-messages-${sessionId}`, JSON.stringify(newMessages))
        }
    }, [sessionId])

    const addMessage = useCallback((type: "user" | "assistant", content: string, sources?: any[]) => {
        const newMessage: Message = {
            id: Date.now().toString(),
            type,
            content,
            timestamp: new Date(),
            sources,
        }

        setMessages((prev) => {
            const updated = [...prev, newMessage]
            if (typeof window !== "undefined") {
                localStorage.setItem("askracha-messages", JSON.stringify(updated))
            }
            return updated
        })
    }, [])



    const handleSubmit = useCallback(
        async (e: React.FormEvent) => {
            e.preventDefault()
            if (!input.trim() || isLoading || !sessionId) return

            const userMessage = input.trim()
            setInput("")
            addMessage("user", userMessage)
            setIsLoading(true)

            try {
                const response = await fetch(`${API_URL}/api/chat/query`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-Chat-Context-Id": sessionId,
                    },
                    body: JSON.stringify({
                        session_id: sessionId,
                        query: userMessage
                    }),
                })

                const data = await response.json()

                if (data.success) {
                    addMessage("assistant", data.response, data.source_nodes)
                } else {
                    addMessage("assistant", `I encountered an issue: ${data.message}`)
                }
            } catch (error) {
                addMessage("assistant", "I'm having trouble connecting to the server. Please ensure the backend is running.")
            }

            setIsLoading(false)
        },
        [input, isLoading, addMessage, sessionId],
    )

    const clearMessages = useCallback(() => {
        setMessages([])
        if (typeof window !== "undefined" && sessionId) {
            localStorage.removeItem(`askracha-messages-${sessionId}`)
        }
    }, [sessionId])

    const resetSession = useCallback(async () => {
        localStorage.removeItem("askracha-session-id")
        document.cookie = "askracha-session-id=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT"
        
        setSessionId("")
        setMessages([])
        router.push("/chat")
    }, [router])

    return {
        messages,
        input,
        setInput,
        isLoading,
        handleSubmit,
        addMessage,
        clearMessages,
        sessionId,
        resetSession,
    }
}
