"use client";

import { Bot, Sparkles } from "lucide-react";
import type { SystemStatus } from "@/types/chat";

interface WelcomeScreenProps {
  status: SystemStatus | null;
  suggestions: string[];
  setInput: (input: string) => void;
}

export function WelcomeScreen({
  status,
  suggestions,
  setInput,
}: WelcomeScreenProps) {
  return (
    <div className="flex-1 flex items-center justify-center p-6">
      <div className="text-center max-w-4xl mx-auto">
        <div className="w-20 h-20 bg-primary rounded-2xl flex items-center justify-center mx-auto mb-8 shadow-lg">
          <Bot className="w-10 h-10 text-primary-foreground" />
        </div>

        <h1 className="text-4xl lg:text-6xl font-bold text-foreground mb-6">
          Welcome to <span className="text-primary">AskRacha</span>
        </h1>

        <div className="flex items-center justify-center gap-2 mb-8">
          <Sparkles className="w-5 h-5 text-primary" />
          <p className="text-xl lg:text-2xl text-muted-foreground">
            Your intelligent Storacha documentation assistant
          </p>
        </div>

        {status && status.documents_loaded && status.documents_loaded > 0 ? (
          <div className="space-y-4">
            <p className="text-muted-foreground mb-8">
              Choose a question to get started, or ask your own:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl mx-auto">
              {suggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => setInput(suggestion)}
                  className="p-6 rounded-lg border border-border bg-card hover:bg-accent text-card-foreground hover:text-accent-foreground transition-colors text-left shadow-sm hover:shadow-md"
                >
                  <div className="text-sm lg:text-base font-medium">
                    {suggestion}
                  </div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="bg-card rounded-lg border border-border p-8 shadow-sm max-w-md mx-auto">
            <p className="text-muted-foreground mb-4">
              Please load the documents to get started
            </p>
            <div className="w-8 h-1 bg-primary rounded-full mx-auto animate-pulse" />
          </div>
        )}
      </div>
    </div>
  );
}
