import { Metadata, ResolvingMetadata } from "next";

interface PageProps {
  params: {
    session_id: string;
  };
}

export async function generateMetadata(
  { params }: PageProps,
  parent: ResolvingMetadata
): Promise<Metadata> {
  const previousMetadata = await parent;
  const sessionId = await Promise.resolve(params.session_id);

  return {
    title: `Chat Session ${sessionId.slice(0, 8)}... - Ask Racha`,
    description: "Chat session with Ask Racha AI assistant",
  };
}

export default async function ChatSessionPage({ params }: PageProps) {
  const sessionId = await Promise.resolve(params.session_id);
  const { ChatSessionWrapper } = require("@/components/chat-session-wrapper");
  return <ChatSessionWrapper initialSessionId={sessionId} />;
}
