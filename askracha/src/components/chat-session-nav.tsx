"use client";

import { useChat } from "@/hooks/use-chat";
import { Button } from "./ui/button";
import { PlusIcon, Share2Icon } from "lucide-react";
import { toast } from "sonner";

export function ChatSessionNav() {
  const { sessionId, resetSession } = useChat();

  const copySessionLink = () => {
    if (sessionId) {
      const url = `${window.location.origin}/chat/${sessionId}`;
      navigator.clipboard.writeText(url);
      toast.success("Chat link copied to clipboard");
    }
  };

  return (
    <div className="flex items-center gap-2">
      <Button
        variant="ghost"
        onClick={resetSession}
        className="text-sm cursor-pointer"
      >
        <PlusIcon className="w-4 h-4 mr-2" />
        New Chat
      </Button>
      {sessionId && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>Session: {sessionId.slice(0, 8)}...</span>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            onClick={copySessionLink}
          >
            <Share2Icon className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
