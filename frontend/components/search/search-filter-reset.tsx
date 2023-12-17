"use client";

import { XMarkIcon } from "@heroicons/react/20/solid";

import { useSearchDispatch } from "@/components/search-provider";

export function ResetSearchFilter() {
  const dispatch = useSearchDispatch()!;

  return (
    <div
      className="rounded-md p-1 hover:bg-accent"
      onClick={() => {
        dispatch({ type: "reset" });
      }}
    >
      <XMarkIcon className="h-4 w-4 shrink-0 text-muted-foreground" />
    </div>
  );
}
