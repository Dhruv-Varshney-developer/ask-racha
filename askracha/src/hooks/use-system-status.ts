"use client"

import { useState, useCallback, useEffect } from "react"
import type { SystemStatus } from "@/types/chat"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"

export interface KnowledgeBaseStatus {
    status: "not_started" | "loading" | "ready" | "error"
    progress: number
    message: string
    documents_loaded: number
}

export function useSystemStatus() {
    const [status, setStatus] = useState<SystemStatus | null>(() => {
        // Load cached status from localStorage
        if (typeof window !== "undefined") {
            const cached = localStorage.getItem("askracha-status")
            return cached ? JSON.parse(cached) : null
        }
        return null
    })

    const [kbStatus, setKbStatus] = useState<KnowledgeBaseStatus>({
        status: "not_started",
        progress: 0,
        message: "Checking knowledge base...",
        documents_loaded: 0
    })

    const [isInitialized, setIsInitialized] = useState(false)
    
    const saveStatus = useCallback((newStatus: SystemStatus) => {
        setStatus(newStatus)
        if (typeof window !== "undefined") {
            localStorage.setItem("askracha-status", JSON.stringify(newStatus))
        }
    }, [])

    const checkStatus = useCallback(async () => {
        try {
            const response = await fetch(`${API_URL}/api/status`)
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json()
            if (data) {
                saveStatus(data)
                setIsInitialized(data.initialized)
            } else {
                console.error("Status data is empty or invalid:", data);
                setIsInitialized(false);
            }
        } catch (error) {
            console.error("Error checking status:", error)
            setStatus(null);
            setIsInitialized(false);
        }
    }, [saveStatus])

    const checkKbStatus = useCallback(async () => {
        try {
            const response = await fetch(`${API_URL}/api/kb-status`)
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json()
            if (data) {
                setKbStatus(data)
                // Update isInitialized based on KB status
                setIsInitialized(data.status === "ready")
            }
        } catch (error) {
            console.error("Error checking KB status:", error)
            setKbStatus({
                status: "error",
                progress: 0,
                message: "Failed to connect to backend",
                documents_loaded: 0
            })
        }
    }, [])

    // Initial status check on mount
    useEffect(() => {
        checkStatus();
        checkKbStatus();
    }, [checkStatus, checkKbStatus]);

    // Poll KB status while loading
    useEffect(() => {
        if (kbStatus.status === "loading") {
            const interval = setInterval(() => {
                checkKbStatus();
            }, 2000); // Poll every 2 seconds

            return () => clearInterval(interval);
        }
    }, [kbStatus.status, checkKbStatus]);

    return {
        status,
        isInitialized,
        checkStatus,
        kbStatus,
        checkKbStatus
    }
}