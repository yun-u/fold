"use client";

import { BookmarkIcon } from "@heroicons/react/20/solid";

import { SearchFilterButton } from "./search-filter-button";

import { useSearchDispatch, SearchParams } from "@/components/search-provider";

interface BookmarkedSearchFilterProps {
  value: SearchParams["bookmarked"];
}

export function BookmarkedSearchFilter({ value }: BookmarkedSearchFilterProps) {
  const dispatch = useSearchDispatch()!;

  return (
    <SearchFilterButton
      enabled={!!value}
      onClick={() => {
        dispatch({ type: "bookmarked", value: !value });
      }}
    >
      <BookmarkIcon className="mr-1 h-3 w-3" />
      Bookmarked
    </SearchFilterButton>
  );
}
