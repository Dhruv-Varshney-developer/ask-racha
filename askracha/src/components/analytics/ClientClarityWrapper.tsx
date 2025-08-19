"use client";

import dynamic from "next/dynamic";

// Dynamic import with SSR disabled to prevent server-side execution
const ClarityPageViewTracker = dynamic(
  () => import("@/components/analytics/ClarityPageViewTracker"),
  {
    ssr: false,
  }
);

export default function ClientClarityWrapper() {
  return <ClarityPageViewTracker />;
}