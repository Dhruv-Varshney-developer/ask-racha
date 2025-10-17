"use client";

import { useState, useEffect } from "react";
import { ChatHeader } from "./chat-header";
import { ChatSidebar } from "./chat-sidebar";
import { ChatMessages } from "./chat-messages";
import { ChatInput } from "./chat-input";
import { WelcomeScreen } from "./welcome-screen";
import { ChatSessionNav } from "./chat-session-nav";
import { useChat } from "@/hooks/use-chat";
import { useSystemStatus } from "@/hooks/use-system-status";
import { useTheme } from "next-themes";

interface AskRachaChatProps {
  initialSessionId?: string;
}

export function AskRachaChat({ initialSessionId }: AskRachaChatProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const {
    messages,
    input,
    setInput,
    isLoading: isChatLoading,
    handleSubmit,
  } = useChat();
  const {
    status,
    isInitialized,
    checkStatus,
  } = useSystemStatus();
  const { theme } = useTheme(); // Get the current theme

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  const suggestions = [
    "What is Storacha and how does it work?",
    "How do I get started with the w3up client?",
    "What are the main concepts in Storacha?",
    "How do I upload files to Storacha?",
    "What are the pricing plans for Storacha?",
  ];

  return (
    // Main container for the whole chat layout
    // Conditionally apply the custom gradient class for 'storacha' theme,
    // otherwise use the solid background from theme variables.
    <div
      className={`flex h-screen md:w-full overflow-x-hidden ${
        theme === "storacha"
          ? "bg-storacha-gradient" // Apply the custom gradient class
          : "bg-background" // Use theme's solid background for other themes (light/dark)
      }`}
    >
      {/* Animated Background */}
      {/* Only show animated background for the 'storacha' theme, using theme-aware colors */}
      {theme === "storacha" && (
        <div className="absolute inset-0 opacity-20 pointer-events-none">
          {/* These gradients and blobs now use theme-defined primary/secondary colors */}
          <div className="absolute inset-0 bg-gradient-to-r from-primary/20 to-secondary/20 animate-pulse"></div>
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl animate-bounce"></div>
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-secondary/10 rounded-full blur-3xl animate-bounce delay-1000"></div>
        </div>
      )}
      {/* If not storacha, these animated backgrounds are not rendered, or you can add different ones */}

      {/* Sidebar (its overflow handling is separate) */}
      <ChatSidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        status={status}
        isInitialized={isInitialized}
        suggestions={suggestions}
        setInput={setInput}
      />

      {/* Main Content Area: flex-1 to take available space */}
      <div className="flex-1 flex flex-col min-w-0">
        <ChatHeader
          onMenuClick={() => setSidebarOpen(true)}
          status={status}
          isInitialized={isInitialized}
        >
          <ChatSessionNav />
        </ChatHeader>

        {/* Content area that holds messages or welcome screen */}
        <div className="flex-1 overflow-x-hidden max-w-full">
          {messages.length === 0 ? (
            <WelcomeScreen
              status={status}
              suggestions={suggestions}
              setInput={setInput}
            />
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
          status={status}
        />
      </div>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/80 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}
