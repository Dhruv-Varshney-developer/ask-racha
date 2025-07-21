"use client"

import type React from "react"

import { useState, useCallback } from "react"
import type { Message } from "@/types/chat"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"

export function useChat() {
    const [messages, setMessages] = useState<Message[]>(() => {
        // Load messages from localStorage on initialization
        if (typeof window !== "undefined") {
            const saved = localStorage.getItem("askracha-messages")
            return saved ? JSON.parse(saved) : []
        }
        return []
    })

    const [input, setInput] = useState("")
    const [isLoading, setIsLoading] = useState(false)

    // Save messages to localStorage whenever they change
    const saveMessages = useCallback((newMessages: Message[]) => {
        setMessages(newMessages)
        if (typeof window !== "undefined") {
            localStorage.setItem("askracha-messages", JSON.stringify(newMessages))
        }
    }, [])

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
            if (!input.trim() || isLoading) return

            const userMessage = input.trim()
            setInput("")
            addMessage("user", userMessage)
            setIsLoading(true)

            try {
                const response = await fetch(`${API_URL}/api/query`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ question: userMessage }),
                })

                const data = await response.json()

                if (data.success) {
                    addMessage("assistant", data.answer, data.sources)
                } else {
                    addMessage("assistant", `I encountered an issue: ${data.message}`)
                }
            } catch (error) {
                addMessage("assistant", "I'm having trouble connecting to the server. Please ensure the backend is running.")
            }

            setIsLoading(false)
        },
        [input, isLoading, addMessage],
    )

    const clearMessages = useCallback(() => {
        setMessages([])
        if (typeof window !== "undefined") {
            localStorage.removeItem("askracha-messages")
        }
    }, [])

    return {
        messages,
        input,
        setInput,
        isLoading,
        handleSubmit,
        addMessage,
        clearMessages,
    }
}
