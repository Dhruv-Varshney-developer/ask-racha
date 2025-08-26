"use client";

import {
  X,
  Sparkles,
  Database,
  Brain,
  FileText,
  Globe,
  Loader2,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import type { SystemStatus } from "@/types/chat";
import { useTheme } from "next-themes"; // Import useTheme to access current theme

interface ChatSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  status: SystemStatus | null;
  isInitialized: boolean;
  suggestions: string[];
  setInput: (input: string) => void;
}

export function ChatSidebar({
  isOpen,
  onClose,
  status,
  isInitialized,
  suggestions,
  setInput,
}: ChatSidebarProps) {
  const { theme } = useTheme(); // Get the current theme

  return (
    <>
      <aside
        className={`
          fixed lg:relative z-50 lg:z-0 h-full w-80 lg:w-96
          border-r border-border
          transform transition-transform duration-300 ease-in-out
          ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
          ${theme === "storacha"
            ? "bg-sidebar-storacha-gradient backdrop-blur-none" // Apply gradient and ensure no blur. Removed bg-opacity-100 as it's for solid colors.
            : "bg-[hsl(var(--sidebar))] backdrop-blur-none" // Directly use HSL color for solid background and ensure no blur. Removed bg-opacity-100.
          }
        `}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-sidebar-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-sidebar-primary rounded-lg flex items-center justify-center shadow-sm">
              <Sparkles className="w-5 h-5 text-sidebar-primary-foreground" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-sidebar-foreground">
                AskRacha
              </h2>
              <p className="text-sm text-sidebar-foreground/70">AI Assistant</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground h-10 w-10"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* System Status */}
          <div className="rounded-lg border bg-card p-6">
            <h3 className="font-semibold text-sidebar-foreground mb-4 flex items-center gap-2">
              <Database className="w-5 h-5 text-primary" />
              System Status
            </h3>

            <div className="space-y-4">
              <StatusItem
                label="System"
                icon={isInitialized ? CheckCircle : Loader2}
                iconColor={isInitialized ? "text-green-600" : "text-orange-600"}
                value={isInitialized ? "Ready" : "Initializing"}
                isLoading={!isInitialized}
              />

              {status && (
                <>
                  <StatusItem
                    label="Documents"
                    icon={FileText}
                    iconColor="text-blue-600"
                    value={status.documents_loaded?.toString() || "0"}
                  />
                  <StatusItem
                    label="Vector Index"
                    icon={status.index_ready ? CheckCircle : AlertCircle}
                    iconColor={
                      status.index_ready
                        ? "text-green-600"
                        : "text-muted-foreground"
                    }
                    value={status.index_ready ? "Ready" : "Pending"}
                  />
                </>
              )}
            </div>

            {status?.model_info && (
              <div className="mt-4 pt-4 border-t border-sidebar-border">
                <p className="text-xs text-sidebar-foreground/70">
                  Model: {status.model_info.llm}
                </p>
              </div>
            )}
          </div>



          {/* Quick Start */}
          {status && status.documents_loaded > 0 && (
            <div className="rounded-lg border border-sidebar-border bg-sidebar-accent/50 p-6">
              <h3 className="font-semibold text-sidebar-foreground mb-4 flex items-center gap-2">
                <Brain className="w-5 h-5 text-primary" />
                Quick Start
              </h3>
              <div className="space-y-3">
                {suggestions.slice(0, 3).map((suggestion, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setInput(suggestion);
                      onClose();
                    }}
                    className="w-full text-left p-4 rounded-md bg-sidebar text-sidebar-foreground hover:text-sidebar-accent-foreground text-sm transition-colors border border-sidebar-border hover:border-sidebar-border/80 hover:bg-sidebar/50 cursor-pointer hover:border-white"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}

function StatusItem({
  label,
  icon: Icon,
  iconColor,
  value,
  isLoading = false,
}: {
  label: string;
  icon: any;
  iconColor: string;
  value: string;
  isLoading?: boolean;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sidebar-foreground/70 text-sm">{label}</span>
      <div className="flex items-center gap-2">
        <Icon
          className={`h-4 w-4 ${iconColor} ${isLoading ? "animate-spin" : ""}`}
        />
        <span className="text-sidebar-foreground text-sm font-medium">
          {value}
        </span>
      </div>
    </div>
  );
}
