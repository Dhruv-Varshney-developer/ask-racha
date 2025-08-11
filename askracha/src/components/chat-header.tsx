"use client";

import { Menu, Sparkles, CheckCircle, Clock } from "lucide-react";
import { ThemeToggle } from "./theme-toggle";
import type { SystemStatus } from "@/types/chat";

interface ChatHeaderProps {
  onMenuClick: () => void;
  status: SystemStatus | null;
  isInitialized: boolean;
}

export function ChatHeader({
  onMenuClick,
  status,
  isInitialized,
}: ChatHeaderProps) {
  return (
    <header className="border-b  bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex items-center justify-between px-4 lg:px-6 py-4">
        {/* Left side */}
        <div className="flex items-center gap-4">
          <button
            onClick={onMenuClick}
            className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-10 w-10 lg:hidden"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center shadow-sm">
              <Sparkles className="w-5 h-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-xl lg:text-2xl font-semibold text-foreground">
                AskRacha
              </h1>
              <p className="text-sm text-muted-foreground hidden sm:block">
                AI Documentation Assistant
              </p>
            </div>
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-3">
          {/* Status indicator */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary text-secondary-foreground border">
            {isInitialized &&
              status?.documents_loaded &&
              status.documents_loaded > 0 ? (
              <>
                <CheckCircle className="w-4 h-4 text-green-600" />{" "}
                {/* Specific status color */}
                <span className="text-sm font-medium">Ready</span>
              </>
            ) : (
              <>
                <Clock className="w-4 h-4 text-orange-600 animate-pulse" />{" "}
                {/* Specific status color */}
                <span className="text-sm font-medium">Initializing</span>
              </>
            )}
          </div>

          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
