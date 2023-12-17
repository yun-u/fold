"use client";

import { useQuery } from "@tanstack/react-query";

import Image from "next/image";
import { useEffect } from "react";

import { PostList } from "@/components/post";
import { Error } from "@/components/post/error";
import { fetchPost } from "@/components/post/fetch-post";
import { Loading } from "@/components/post/loading";
import { NoResult } from "@/components/post/no-result";
import { renderPost } from "@/components/post/render-post";
import { useSearchDispatch } from "@/components/search-provider";

export function Main({ documentId }: { documentId: string }) {
  const dispatch = useSearchDispatch()!;

  useEffect(() => {
    dispatch({ type: "vector_search_document", value: documentId });
  }, [documentId, dispatch]);

  const query = useQuery({
    queryKey: ["post", documentId],
    queryFn: () => fetchPost(documentId),
  });

  if (query.isLoading) {
    return <Loading />;
  }

  if (query.isError) {
    return <Error message={(query.error as Error).message} />;
  }

  // We can assume by this point that `isSuccess === true`
  const posts = query.data.data;

  return (
    <div className="h-[100dvh] pt-28">
      {posts.length > 0 ? (
        <div className="flex h-full flex-col">
          <div className="bg-secondary/50">{renderPost(posts[0])}</div>
          <div className="flex flex-col items-center bg-gradient-to-b from-secondary/50 to-background pb-4 pt-4">
            <Image
              src="/logo.svg"
              alt="Logo"
              className="-translate-y-1/2 -rotate-45 dark:invert"
              width={24}
              height={24}
              priority
              draggable={false}
            />
          </div>
          <PostList count={10} />
        </div>
      ) : (
        <NoResult />
      )}
    </div>
  );
}
