"use client";

import type React from "react";
import { Send } from "lucide-react";
import { useRef, useEffect, useState } from "react";

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

  const handleKeyDown = async (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      await handleSubmit(e);
    }
  };

  useEffect(() => {
    if (!isLoading) {
      textareaRef.current?.focus();
    }
  }, [isLoading]);

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
            autoFocus
            placeholder={
              canSubmit
                ? "Ask me anything about Storacha..."
                : "Please load documents first..."
            }
            disabled={!canSubmit || isLoading}
            className="flex w-full rounded-lg bg-background/5 backdrop-blur-sm text-sm
              placeholder:text-muted-foreground/50
              disabled:cursor-not-allowed disabled:opacity-50
              resize-none min-h-[52px] max-h-[120px] px-4 lg:px-6 py-3 lg:py-4
              border border-transparent
              focus:outline-none focus:ring-1 focus:ring-primary/20 focus:border-primary/20
              transition-all duration-200"
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
