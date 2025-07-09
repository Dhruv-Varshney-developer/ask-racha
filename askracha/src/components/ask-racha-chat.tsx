// "use client" // Already there

import { useState, useEffect } from "react"
import { ChatHeader } from "./chat-header"
import { ChatSidebar } from "./chat-sidebar"
import { ChatMessages } from "./chat-messages"
import { ChatInput } from "./chat-input"
import { WelcomeScreen } from "./welcome-screen"
import { useChat } from "@/hooks/use-chat"
import { useSystemStatus } from "@/hooks/use-system-status"

export function AskRachaChat() {
    const [sidebarOpen, setSidebarOpen] = useState(false)
    const { messages, input, setInput, isLoading: isChatLoading, handleSubmit } = useChat()
    const { status, isInitialized, checkStatus, initializeRAG, loadDefaultDocuments, loadingDocuments } = useSystemStatus()

    useEffect(() => {
        checkStatus()
        initializeRAG()
    }, [checkStatus, initializeRAG])

    const suggestions = [
        "What is Storacha and how does it work?",
        "How do I get started with the w3up client?",
        "What are the main concepts in Storacha?",
        "How do I upload files to Storacha?",
        "What are the pricing plans for Storacha?",
    ]

    return (
        // Main container for the whole chat layout
        // 'md:w-full' ensures it takes full width above medium screens.
        // 'h-screen' ensures it takes full viewport height.
        // 'overflow-x-hidden' on this root div is crucial for mobile.
        <div className="flex h-screen bg-background md:w-full overflow-x-hidden">
            {/* Sidebar (its overflow handling is separate) */}
            <ChatSidebar
                isOpen={sidebarOpen}
                onClose={() => setSidebarOpen(false)}
                status={status}
                isInitialized={isInitialized}
                isLoading={loadingDocuments}
                loadDefaultDocuments={async () => { await loadDefaultDocuments(); }}
                suggestions={suggestions}
                setInput={setInput}
            />

            {/* Main Content Area: flex-1 to take available space */}
            <div className="flex-1 flex flex-col min-w-0"> {/* min-w-0 here is also important for flex items */}
                <ChatHeader onMenuClick={() => setSidebarOpen(true)} status={status} isInitialized={isInitialized} />

                {/* Content area that holds messages or welcome screen */}
                {/* overflow-x-hidden is paramount here to ensure its content doesn't break */}
                <div className="flex-1 overflow-x-hidden max-w-full"> {/* Changed max-w-screen to max-w-full */}
                    {messages.length === 0 ? (
                        <WelcomeScreen status={status} suggestions={suggestions} setInput={setInput} />
                    ) : (
                        <ChatMessages messages={messages} isLoading={isChatLoading} />
                    )}
                </div>

                <ChatInput
                    input={input}
                    setInput={setInput}
                    handleSubmit={handleSubmit}
                    isLoading={isChatLoading}
                    canSubmit={!!status?.documents_loaded}
                    status={status} // Pass status if ChatInput uses it, otherwise remove 'status={undefined}'
                />
            </div>

            {/* Mobile overlay */}
            {sidebarOpen && (
                <div className="fixed inset-0 bg-black/80 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />
            )}
        </div>
    )
}