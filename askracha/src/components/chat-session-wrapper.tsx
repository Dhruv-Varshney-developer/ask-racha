"use client";

import { AskRachaChat } from "./ask-racha-chat";

interface ChatSessionWrapperProps {
  initialSessionId?: string;
}

export function ChatSessionWrapper({ initialSessionId }: ChatSessionWrapperProps) {
  return <AskRachaChat initialSessionId={initialSessionId} />;
}
