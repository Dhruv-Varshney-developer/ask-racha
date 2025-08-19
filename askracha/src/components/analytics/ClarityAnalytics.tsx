"use client";

import { useEffect } from "react";

const ClarityAnalytics = () => {
  useEffect(() => {
    // Ensure we're in a browser environment
    if (typeof window === "undefined" || typeof document === "undefined") {
      return;
    }

    const projectId = process.env.NEXT_PUBLIC_CLARITY_PROJECT_ID;

    // Handle missing configuration gracefully
    if (!projectId || typeof projectId !== "string" || projectId.trim() === "") {
      if (process.env.NODE_ENV === "development") {
        console.warn("Microsoft Clarity: Project ID not configured or invalid. Set NEXT_PUBLIC_CLARITY_PROJECT_ID environment variable.");
      }
      return;
    }

    // Check if Clarity script is already loaded
    if (window.clarity && typeof window.clarity === "function") {
      if (process.env.NODE_ENV === "development") {
        console.log("Microsoft Clarity: Already initialized");
      }
      return;
    }

    try {
      // Validate project ID format (basic validation)
      if (!/^[a-zA-Z0-9]+$/.test(projectId)) {
        if (process.env.NODE_ENV === "development") {
          console.error("Microsoft Clarity: Invalid project ID format");
        }
        return;
      }

      // Microsoft Clarity tracking script injection with enhanced error handling
      (function (c: any, l: any, a: any, r: any, i: any) {
        try {
          c[a] = c[a] || function () {
            (c[a].q = c[a].q || []).push(arguments);
          };

          const t = l.createElement(r);
          if (!t) {
            throw new Error("Failed to create script element");
          }

          t.async = 1;
          t.src = "https://www.clarity.ms/tag/" + encodeURIComponent(i);

          // Add error handling for script loading
          t.onerror = function () {
            if (process.env.NODE_ENV === "development") {
              console.error("Microsoft Clarity: Failed to load script from CDN");
            }
          };

          const y = l.getElementsByTagName(r)[0];
          if (y && y.parentNode) {
            y.parentNode.insertBefore(t, y);
          } else {
            // Fallback: append to head if no script tags exist
            const head = l.getElementsByTagName('head')[0];
            if (head) {
              head.appendChild(t);
            }
          }
        } catch (scriptError) {
          if (process.env.NODE_ENV === "development") {
            console.error("Microsoft Clarity: Script injection failed", scriptError);
          }
        }
      })(window, document, "clarity", "script", projectId);

      if (process.env.NODE_ENV === "development") {
        console.log("Microsoft Clarity: Initialization attempted with project ID:", projectId);
      }
    } catch (error) {
      // Graceful error handling - don't break the application
      if (process.env.NODE_ENV === "development") {
        console.error("Microsoft Clarity: Failed to initialize", error);
      }
      // In production, silently continue without breaking the app
    }
  }, []);

  return null;
};

export default ClarityAnalytics;