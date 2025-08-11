"use client";

import { useRef, useEffect } from "react";
import { Bot, User, ExternalLink, Loader2 } from "lucide-react";
import { useTheme } from "next-themes";
import type { Message } from "@/types/chat";

// Import ReactMarkdown and remarkGfm
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface ChatMessagesProps {
  messages: Message[];
  isLoading: boolean;
}

export function ChatMessages({ messages, isLoading }: ChatMessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    // Use requestAnimationFrame to ensure scroll happens after potential DOM updates
    requestAnimationFrame(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    // Added 'flex-col' for explicit column direction for consistent spacing
    // 'overflow-x-hidden' is good here to prevent horizontal scroll from messages themselves.
    <div className="flex flex-col flex-1 overflow-y-auto p-3 sm:p-4 lg:p-6 space-y-4 sm:space-y-6 overflow-x-hidden">
      {messages.map((message) => (
        <ChatMessage key={message.id} message={message} />
      ))}

      {isLoading && <LoadingMessage />}
      <div ref={messagesEndRef} />
    </div>
  );
}

function ChatMessage({ message }: { message: Message }) {
  const isUser = message.type === "user";
  const { theme } = useTheme();
  
  // Get theme-specific prose classes with responsive spacing
  const getProseClasses = () => {
    const baseClasses = "prose prose-sm sm:prose-base lg:prose-lg max-w-none leading-relaxed";
    
    if (theme === "storacha") {
      return `${baseClasses} prose-storacha`;
    } else if (theme === "dark") {
      return `${baseClasses} dark:prose-invert`;
    } else {
      return baseClasses;
    }
  };

  return (
    // The parent flex container for the message bubble
    // max-w-[calc(100%-4rem)] or max-w-[90%] ensures it doesn't hit the very edge on small screens.
    // The original ml-4/mr-4 handles spacing.
    <div
      className={`flex ${
        isUser ? "justify-end" : "justify-start"
      } animate-in slide-in-from-bottom-4 duration-500`}
    >
      <div
        className={`max-w-[calc(100%-2rem)] sm:max-w-[calc(100%-4rem)] md:max-w-4xl rounded-lg border p-4 lg:p-6 shadow-sm ${
          isUser
            ? "bg-primary text-primary-foreground ml-2 sm:ml-4 lg:ml-12 border-primary"
            : "bg-card text-card-foreground mr-2 sm:mr-4 lg:mr-12 border-border"
        }`}
      >
        <div className="flex items-start gap-4">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
              isUser ? "bg-primary/20" : "bg-primary" // Changed bg-primary-foreground/20 to bg-primary/20 for user icon background
            }`}
          >
            {isUser ? (
              <User className={`w-4 h-4 text-primary-foreground`} />
            ) : (
              <Bot className="w-4 h-4 text-primary-foreground" />
            )}
          </div>

          {/* Enhanced message content with improved typography */}
          <div className="flex-1 min-w-0">
            <div className={`${getProseClasses()} text-sm lg:text-base`}>
              {/* <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={{
                  // Custom component overrides for better formatting
                  pre: ({ children, ...props }) => (
                    <pre {...props} className="overflow-x-auto whitespace-pre-wrap break-words">
                      {children}
                    </pre>
                  ),
                  code: ({ children, ...props }: any) => {
                    const { inline } = props;
                    return inline ? (
                      <code {...props} className="whitespace-nowrap">
                        {children}
                      </code>
                    ) : (
                      <code {...props}>
                        {children}
                      </code>
                    );
                  },
                }}
              >
                {message.content}
              </ReactMarkdown> */}
              <ReactMarkdown
  remarkPlugins={[remarkGfm]}
  components={{
    pre: ({ children }) => {
      // Safely extract text from children
      let text = '';
      if (children && typeof children === 'object') {
        // Recursively extract text from React nodes
        const getText = (node: React.ReactNode): void => {
          if (node == null) return;
          if (typeof node === 'string') {
            text += node;
          } else if (Array.isArray(node)) {
            node.forEach(getText);
          } else if (typeof node === 'object' && 'props' in node) {
            getText((node as any).props.children);
          }
        };
        getText(children);
      }

      const handleCopy = () => {
        navigator.clipboard.writeText(text).catch(err => {
          console.error('Failed to copy:', err);
        });
      };

      return (
        <div className="group relative my-4">
          <pre className="overflow-x-auto rounded-lg border border-border bg-secondary p-4 font-mono text-sm leading-relaxed shadow-sm">
            {children}
          </pre>
          <button
            type="button"
            onClick={handleCopy}
            className="absolute right-2 top-2 opacity-0 transition-opacity group-hover:opacity-100 focus:opacity-100 hover:bg-secondary/50 rounded px-2 py-1 text-xs text-muted-foreground hover:text-foreground"
            aria-label="Copy code"
          >
            Copy
          </button>
        </div>
      );
    },
    code({ node, inline, className, children, ...props }: any) {
      if (inline) {
        return (
          <code
            className="rounded border border-border bg-secondary px-1.5 py-0.5 text-sm font-medium"
            {...props}
          >
            {children}
          </code>
        );
      }

      return (
        <code className="font-mono text-sm" {...props}>
          {children}
        </code>
      );
    },
  }}
>
  {message.content}
</ReactMarkdown>
            </div>

            {message.sources && message.sources.length > 0 && (
              <div className="mt-4 pt-4 border-t border-border">
                <p className="text-sm font-medium text-muted-foreground mb-3 flex items-center gap-2">
                  <ExternalLink className="w-4 h-4" />
                  Sources:
                </p>
                <div className="space-y-2">
                  {message.sources.map((source, idx) => (
                    <a
                      key={idx}
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block p-3 rounded-md bg-muted hover:bg-muted/80 text-sm text-primary hover:text-primary/80 transition-colors border border-border hover:border-border/80"
                    >
                      <div className="font-medium">{source.title}</div>
                      {/* Truncate long URLs to prevent overflow */}
                      <div className="text-xs text-muted-foreground mt-1 truncate">
                        {source.url}
                      </div>
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function LoadingMessage() {
  return (
    <div className="flex justify-start animate-in slide-in-from-bottom-4 duration-500">
      <div className="bg-card text-card-foreground border border-border rounded-lg p-6 flex items-center gap-4 shadow-sm mr-4 lg:mr-12">
        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
          <Bot className="w-4 h-4 text-primary-foreground" />
        </div>
        <div className="flex items-center gap-3">
          <Loader2 className="h-5 w-5 animate-spin text-primary" />
          <span className="text-muted-foreground">Thinking...</span>
        </div>
      </div>
    </div>
  );
}
