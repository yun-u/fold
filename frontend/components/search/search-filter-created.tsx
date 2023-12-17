"use client";

import { ArrowDownIcon } from "@heroicons/react/20/solid";

import { SearchFilterButton } from "./search-filter-button";

import { useSearchDispatch, SearchParams } from "@/components/search-provider";
import { cn } from "@/lib/utils";

interface CreatedSearchFilterProps {
  value: SearchParams["desc"];
  disabled?: boolean;
}

export function CreatedSearchFilter({
  value,
  disabled = false,
}: CreatedSearchFilterProps) {
  const dispatch = useSearchDispatch()!;

  return (
    <SearchFilterButton
      enabled
      disabled={disabled}
      onClick={() => {
        dispatch({ type: "desc", value: !value });
      }}
    >
      <ArrowDownIcon
        className={cn(
          "mr-1 h-3 w-3 transition-transform",
          !value && !disabled ? "rotate-180" : "",
        )}
      />
      Created
    </SearchFilterButton>
  );
}
