"use client";

import type React from "react";
import { Send } from "lucide-react";
import { useRef, useEffect } from "react";

interface ChatInputProps {
  input: string;
  setInput: (input: string) => void;
  handleSubmit: (e: React.FormEvent) => Promise<void>;
  isLoading: boolean;
  canSubmit: boolean;
  status: any; // TODO: Type this properly
}

export function ChatInput({
  input,
  setInput,
  handleSubmit,
  isLoading,
  canSubmit,
  status,
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [input]);

  return (
    <div className="p-4 lg:p-6 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-t">
      <form
        onSubmit={handleSubmit}
        className="flex gap-3 lg:gap-4 max-w-4xl mx-auto"
      >
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              adjustTextareaHeight();
            }}
            onKeyDown={handleKeyDown}
            placeholder={
              canSubmit
                ? "Ask me anything about Storacha..."
                : "Please load documents first..."
            }
            disabled={!canSubmit || isLoading}
            className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none min-h-[52px] max-h-[120px] px-4 lg:px-6 py-3 lg:py-4"
            rows={1}
          />
        </div>

        <button
          type="submit"
          disabled={!input.trim() || !canSubmit || isLoading}
          className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-12 w-12 shrink-0"
        >
          <Send className="h-5 w-5" />
        </button>
      </form>
    </div>
  );
}
