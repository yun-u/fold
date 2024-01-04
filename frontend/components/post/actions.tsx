"use client";

import { CheckCircleIcon, XCircleIcon } from "@heroicons/react/20/solid";
import {
  BookmarkIcon,
  FireIcon,
  TrashIcon,
  ArrowTopRightOnSquareIcon,
} from "@heroicons/react/24/solid";
import {
  useMutation,
  MutationFunction,
  useQueryClient,
} from "@tanstack/react-query";
import { curry } from "lodash";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { useToast } from "@/components/ui/use-toast";
import { PostPage } from "@/lib/types";
import { cn } from "@/lib/utils";

async function requestAction(
  url: URL,
  method: "POST" | "DELETE",
  params: Record<string, unknown>,
): Promise<{ success: boolean }> {
  try {
    const response = await fetch(url, {
      method: method,
      cache: "no-cache",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      // Check for non-successful HTTP status codes
      const errorMessage = await response.text(); // Extract the error message from the response body
      throw new Error(
        `HTTP error: Status: ${response.status}, Message: ${errorMessage}`,
      );
    }

    return await response.json();
  } catch (error) {
    console.error("Error:", error);
    throw error; // Re-throw the error if you want to handle it further up the call stack
  }
}

interface ActionButtonProps extends React.ComponentProps<"button"> {
  documentId: string;
  icon: (isOn: boolean) => JSX.Element;
  mutationFn: MutationFunction;
  on: boolean;
}

function refetchPage(
  documentId: string,
  lastPage: PostPage,
  _index: number,
  _allPages: PostPage[],
) {
  const shouldRefetch =
    lastPage.data.filter((post) => post.document_id == documentId).length > 0;
  return shouldRefetch;
}

function ActionButton({
  documentId,
  icon,
  mutationFn,
  on,
  className,
}: ActionButtonProps) {
  const { toast } = useToast();

  const [isEnabled, setIsEnbaled] = useState(on);
  const queryClient = useQueryClient();

  useEffect(() => {
    setIsEnbaled(on);
  }, [on]);

  const mutation = useMutation({
    mutationFn: mutationFn,
    onSuccess: () => {
      queryClient.refetchQueries<PostPage>({
        refetchPage: curry(refetchPage)(documentId),
      });

      // TODO: Add 'Undo' button
      toast({
        description: (
          <div className="flex items-center gap-2 text-base">
            <CheckCircleIcon className="h-4 w-4 shrink-0 fill-emerald-500" />
            <div>{`Successfully ${!isEnabled ? "marked" : "unmarked"}.`}</div>
          </div>
        ),
        className: "shadow-lg",
      });
    },
    onError: () => {
      toast({
        description: (
          <div className="flex items-center gap-2 text-base">
            <XCircleIcon className="h-4 w-4 shrink-0 fill-rose-500" />
            <div>Request failed.</div>
          </div>
        ),
        className: "shadow-lg",
      });
    },
  });

  return (
    <button
      className={cn("h-fit w-fit", className)}
      onClick={() => {
        mutation.mutate({ id: documentId, state: !isEnabled });
      }}
    >
      {icon(isEnabled)}
    </button>
  );
}

export interface Actions {
  documentId: string;
  isRead: boolean;
  isBookmarked: boolean;
}

export function Actions({ documentId, isRead, isBookmarked }: Actions) {
  return (
    <div className="px-4 pt-2">
      <div className="flex items-start justify-between">
        <ActionButton
          className="justify-self-start"
          documentId={documentId}
          icon={(isOn) => (
            <FireIcon
              className={cn(
                "h-6 w-6 shrink-0 transition-colors",
                isOn
                  ? "fill-red-400 dark:fill-red-500"
                  : "fill-zinc-300 hover:fill-zinc-400 dark:fill-zinc-800 dark:hover:fill-zinc-700",
              )}
            />
          )}
          mutationFn={
            curry(requestAction)(
              new URL(`/api/read`, window.location.origin),
              "POST",
            ) as MutationFunction
          }
          on={isRead}
        />
        <ActionButton
          className="justify-self-center"
          documentId={documentId}
          icon={(isOn) => (
            <BookmarkIcon
              className={cn(
                "h-6 w-6 shrink-0 transition-colors",
                isOn
                  ? "fill-sky-400 dark:fill-sky-500"
                  : "fill-zinc-300 hover:fill-zinc-400 dark:fill-zinc-800 dark:hover:fill-zinc-700",
              )}
            />
          )}
          mutationFn={
            curry(requestAction)(
              new URL(`/api/bookmark`, window.location.origin),
              "POST",
            ) as MutationFunction
          }
          on={isBookmarked}
        />
        <div className="justify-self-center">
          <LinkButton documentId={documentId} />
        </div>
        <div className="justify-self-end">
          <DeleteButton documentId={documentId} />
        </div>
      </div>
    </div>
  );
}

function LinkButton({ documentId }: { documentId: string }) {
  return (
    <Link
      target="_blank"
      href={`/${documentId}`}
      className="break-all leading-none underline decoration-1 hover:decoration-2"
    >
      <ArrowTopRightOnSquareIcon className="h-6 w-6 fill-zinc-300 transition-colors hover:fill-zinc-400 dark:fill-zinc-800 dark:hover:fill-zinc-700" />
    </Link>
  );
}

function DeleteButton({ documentId }: { documentId: string }) {
  const queryClient = useQueryClient();
  return (
    <AlertDialog>
      <AlertDialogTrigger>
        <TrashIcon className="h-6 w-6 fill-zinc-300 transition-colors hover:fill-zinc-400 dark:fill-zinc-800 dark:hover:fill-zinc-700" />
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
          <AlertDialogDescription>
            This action cannot be undone. This will permanently delete post.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction asChild>
            <button
              onClick={() => {
                requestAction(
                  new URL(`/api/document`, window.location.origin),
                  "DELETE",
                  {
                    id: documentId,
                  },
                ).then(() => {
                  queryClient.refetchQueries<PostPage>({
                    refetchPage: curry(refetchPage)(documentId),
                  });
                });
              }}
            >
              Delete
            </button>
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
