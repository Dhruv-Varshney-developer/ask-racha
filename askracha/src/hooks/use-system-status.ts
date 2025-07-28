"use client"

import { useState, useCallback, useEffect } from "react" // Import useEffect here
import type { SystemStatus } from "@/types/chat"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"

export function useSystemStatus() {
    const [status, setStatus] = useState<SystemStatus | null>(() => {
        // Load cached status from localStorage
        if (typeof window !== "undefined") {
            const cached = localStorage.getItem("askracha-status")
            return cached ? JSON.parse(cached) : null
        }
        return null
    })

    const [isInitialized, setIsInitialized] = useState(false)
    const [loadingDocuments, setLoadingDocuments] = useState(false) // <--- NEW STATE ADDED

    const saveStatus = useCallback((newStatus: SystemStatus) => {
        setStatus(newStatus)
        if (typeof window !== "undefined") {
            localStorage.setItem("askracha-status", JSON.stringify(newStatus))
        }
    }, [])

    const checkStatus = useCallback(async () => {
        try {
            const response = await fetch(`${API_URL}/api/status`)
            if (!response.ok) { // Add error handling for network issues
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json()
            if (data) { // Ensure data is not null/undefined before saving
                saveStatus(data)
                setIsInitialized(data.initialized)
            } else {
                console.error("Status data is empty or invalid:", data);
                setIsInitialized(false);
            }
        } catch (error) {
            console.error("Error checking status:", error)
            setStatus(null); // Clear status on error
            setIsInitialized(false); // Set to false on error
        }
    }, [saveStatus])

    const initializeRAG = useCallback(async () => {
        if (isInitialized) return; // Prevent re-initialization if already done
        try {
            const response = await fetch(`${API_URL}/api/initialize`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
            })
            if (!response.ok) { // Add error handling
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json()

            if (data.success) {
                setIsInitialized(true)
                saveStatus(data.status)
                checkStatus(); // Re-check status after successful initialization
            } else {
                console.error("RAG initialization failed:", data.message);
                setIsInitialized(false);
            }
        } catch (error) {
            console.error("Error initializing RAG:", error)
            setIsInitialized(false); // Set to false on error
        }
    }, [isInitialized, saveStatus, checkStatus]) // Add isInitialized and checkStatus to dependencies

    const loadDefaultDocuments = useCallback(async () => {
        const defaultUrls = [
            "https://docs.storacha.network/quickstart/",
            "https://docs.storacha.network/concepts/ucans-and-storacha/",
        ]

        setLoadingDocuments(true); // <--- Set loading to true when starting
        try {
            const response = await fetch(`${API_URL}/api/load-documents`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ urls: defaultUrls }),
            })

            if (!response.ok) { // Add proper error handling
                const errorData = await response.json();
                throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json()

            if (data.success) {
                await checkStatus()
                return {
                    success: true,
                    message: `✨ Successfully loaded ${data.document_count} documents! I'm ready to help you with Storacha questions.`,
                }
            } else {
                return {
                    success: false,
                    message: `❌ Failed to load documents: ${data.message}`,
                }
            }
        } catch (error: any) { // Use 'any' for now or define a more specific error type
            console.error("Error loading documents:", error)
            return {
                success: false,
                message: `❌ Error loading documents. Please check if the backend server is running. Detail: ${error.message || String(error)}`,
            }
        } finally {
            setLoadingDocuments(false); // <--- Set loading to false when finished (success or error)
        }
    }, [checkStatus])

    // Initial status check on mount
    useEffect(() => {
        checkStatus();
    }, [checkStatus]);

    return {
        status,
        isInitialized,
        loadingDocuments, // <--- EXPOSE THE NEW LOADING STATE
        checkStatus,
        initializeRAG,
        loadDefaultDocuments,
    }
}