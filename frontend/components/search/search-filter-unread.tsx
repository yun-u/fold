"use client";

import { FireIcon } from "@heroicons/react/20/solid";

import { SearchFilterButton } from "./search-filter-button";

import { useSearchDispatch, SearchParams } from "@/components/search-provider";

interface UnreadSearchFilterProps {
  value: SearchParams["unread"];
}

export function UnreadSearchFilter({ value }: UnreadSearchFilterProps) {
  const dispatch = useSearchDispatch()!;

  return (
    <SearchFilterButton
      enabled={!!value}
      onClick={() => {
        dispatch({ type: "unread", value: !value });
      }}
    >
      <FireIcon className="mr-1 h-3 w-3" />
      Unread
    </SearchFilterButton>
  );
}
