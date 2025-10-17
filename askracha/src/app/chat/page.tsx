import { Metadata } from "next";

export const metadata: Metadata = {
  title: "New Chat - Ask Racha",
  description: "Start a new chat session with Ask Racha AI assistant",
};

export default function ChatPage() {
  const { ChatSessionWrapper } = require("@/components/chat-session-wrapper");
  return <ChatSessionWrapper />;
}
