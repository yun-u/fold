"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { useWindowVirtualizer } from "@tanstack/react-virtual";
import { Loader2 } from "lucide-react";
import * as React from "react";

import { fetchPostList } from "./fetch-post-list";

import { Loading } from "./loading";
import { NoResult } from "./no-result";
import { renderPost } from "./render-post";

import { Error } from "@/components/post/error";
import { useSearch } from "@/components/search-provider";

import { cn } from "@/lib/utils";

export function PostList({
  className,
  count,
  overscan = 5,
}: {
  className?: string;
  count: number;
  overscan?: number;
}) {
  const searchParams = useSearch()!;

  const {
    data,
    error,
    fetchNextPage,
    hasNextPage,
    isFetching,
    isFetchingNextPage,
    status,
  } = useInfiniteQuery({
    queryKey: ["posts", searchParams],
    queryFn: (ctx) => fetchPostList(searchParams!, ctx.pageParam, count),
    getNextPageParam: (lastPost, _posts) => lastPost.next_cursor,
  });

  const posts = data ? data.pages.flatMap((x) => x.data) : [];

  const parentRef = React.useRef<HTMLDivElement>(null);
  const parentOffsetRef = React.useRef(0);

  React.useLayoutEffect(() => {
    parentOffsetRef.current = parentRef.current?.offsetTop ?? 0;
  }, []);

  const rowVirtualizer = useWindowVirtualizer({
    count: hasNextPage ? posts.length + 1 : posts.length,
    estimateSize: () => 600,
    scrollMargin: parentOffsetRef.current,
    overscan: overscan,
  });

  const items = rowVirtualizer.getVirtualItems();

  React.useEffect(() => {
    const [lastItem] = [...items].reverse();

    if (!lastItem) {
      return;
    }

    if (
      lastItem.index >= posts.length - 1 &&
      hasNextPage &&
      !isFetchingNextPage
    ) {
      fetchNextPage();
    }
  }, [posts.length, fetchNextPage, hasNextPage, isFetchingNextPage, items]);

  const BackgroundUpdatingLoading = () => (
    <div className="fixed left-1/2 top-1/2 z-40 -translate-x-1/2 -translate-y-1/2">
      <Loader2 className="h-12 w-12 animate-spin text-foreground/80" />
    </div>
  );

  const render = (param: typeof status) => {
    switch (param) {
      case "loading":
        return <Loading />;
      case "error":
        return (
          <div className="container flex h-full flex-col items-center justify-center p-4">
            <Error message={(error as Error).message} />
          </div>
        );
      case "success":
        if (items.length == 0) {
          return <NoResult />;
        }

        return (
          <div
            ref={parentRef}
            className={cn(
              "relative w-full",
              `h-${rowVirtualizer.getTotalSize()}px`,
            )}
          >
            <div
              className="absolute left-0 top-0 w-full"
              style={{
                transform: `translateY(${
                  items[0].start - rowVirtualizer.options.scrollMargin
                }px)`,
              }}
            >
              {items.map((virtualRow, index) => {
                const isLast = items.length - 1 === index;

                const isLoaderRow = virtualRow.index > posts.length - 1;
                const post = posts[virtualRow.index];

                return (
                  <div
                    key={virtualRow.index}
                    data-index={virtualRow.index}
                    ref={rowVirtualizer.measureElement}
                    className={isLast ? "pb-[3.5rem]" : ""}
                  >
                    {isLoaderRow ? (
                      hasNextPage ? (
                        <Loading />
                      ) : null
                    ) : (
                      renderPost(post)
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        );
    }
  };

  return (
    <div className={cn("grow", className)}>
      {isFetching && !isFetchingNextPage ? <BackgroundUpdatingLoading /> : null}
      {render(status)}
    </div>
  );
}
