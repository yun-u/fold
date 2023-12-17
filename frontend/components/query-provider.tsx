"use client";

import {
  QueryClient,
  QueryClientProvider as QueryClientProviderPrimitive,
} from "@tanstack/react-query";
import { useState } from "react";

export function QueryClientProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [queryClient] = useState(() => new QueryClient());

  return (
    <QueryClientProviderPrimitive client={queryClient}>
      {children}
    </QueryClientProviderPrimitive>
  );
}
