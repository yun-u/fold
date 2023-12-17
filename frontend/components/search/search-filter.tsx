"use client";

import { AuthorSearchFilter } from "./search-filter-author";
import { BookmarkedSearchFilter } from "./search-filter-bookmarked";
import { CategorySearchFilter } from "./search-filter-category";
import { CreatedSearchFilter } from "./search-filter-created";
import { ResetSearchFilter } from "./search-filter-reset";
import { TextSerachFilter } from "./search-filter-text";
import { TitleSearchFilter } from "./search-filter-title";
import { UnreadSearchFilter } from "./search-filter-unread";

import { useSearch } from "@/components/search-provider";
import { cn } from "@/lib/utils";

export function SearchFilter({
  className,
  ...props
}: React.HTMLProps<HTMLDivElement>) {
  const searchParams = useSearch()!;

  return (
    <div
      className={cn(
        "flex items-center gap-2 overflow-x-auto px-4 py-4 lg:px-8",
        className,
      )}
      {...props}
    >
      <CreatedSearchFilter
        value={searchParams.desc}
        disabled={
          searchParams.vector_search || searchParams.vector_search_document
            ? true
            : false
        }
      />
      <CategorySearchFilter value={searchParams.category} />
      <UnreadSearchFilter value={searchParams.unread} />
      <BookmarkedSearchFilter value={searchParams.bookmarked} />
      <TextSerachFilter value={searchParams.text} />
      <TitleSearchFilter value={searchParams.title} />
      <AuthorSearchFilter value={searchParams.author} />
      <ResetSearchFilter />
    </div>
  );
}
