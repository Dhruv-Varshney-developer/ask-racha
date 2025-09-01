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

    // Initial status check on mount
    useEffect(() => {
        checkStatus();
    }, [checkStatus]);

    return {
        status,
        isInitialized,
        checkStatus,
    }
}