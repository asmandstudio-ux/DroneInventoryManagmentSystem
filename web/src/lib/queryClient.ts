"use client";

import { QueryClient } from "@tanstack/react-query";

let browserQueryClient: QueryClient | undefined;

export function getQueryClient() {
  if (typeof window === "undefined") {
    // On the server (if used), create a new client per request.
    return new QueryClient();
  }

  // In the browser, reuse the same QueryClient for the life of the tab.
  if (!browserQueryClient) {
    browserQueryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: 1,
          refetchOnWindowFocus: false
        }
      }
    });
  }

  return browserQueryClient;
}

