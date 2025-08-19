"use client";

import { useEffect } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { Suspense } from "react";

const PageViewTracker = () => {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    // Ensure we're in a browser environment
    if (typeof window === "undefined") {
      return;
    }

    // Check if Clarity is available with null safety
    if (!window.clarity || typeof window.clarity !== "function") {
      if (process.env.NODE_ENV === "development") {
        console.warn("Microsoft Clarity: clarity function not available. Make sure ClarityAnalytics component is loaded first.");
      }
      return;
    }

    try {
      // Validate pathname and searchParams
      if (!pathname || typeof pathname !== "string") {
        if (process.env.NODE_ENV === "development") {
          console.warn("Microsoft Clarity: Invalid pathname provided");
        }
        return;
      }

      // Construct full URL with search parameters
      const searchString = searchParams?.toString() || "";
      const url = pathname + (searchString ? `?${searchString}` : "");
      
      // Validate URL before sending
      if (url.length > 2048) {
        if (process.env.NODE_ENV === "development") {
          console.warn("Microsoft Clarity: URL too long, truncating", url.substring(0, 100) + "...");
        }
        return;
      }
      
      // Send page view event to Clarity
      window.clarity("set", "page", url);
      
      if (process.env.NODE_ENV === "development") {
        console.log("Microsoft Clarity: Page view tracked for", url);
      }
    } catch (error) {
      // Graceful error handling - don't break the application
      if (process.env.NODE_ENV === "development") {
        console.error("Microsoft Clarity: Failed to track page view", error);
      }
      // In production, silently continue without breaking the app
    }
  }, [pathname, searchParams]);

  return null;
};

// Wrap the component in Suspense for proper hydration handling
export default function ClarityPageViewTracker() {
  return (
    <Suspense fallback={null}>
      <PageViewTracker />
    </Suspense>
  );
}