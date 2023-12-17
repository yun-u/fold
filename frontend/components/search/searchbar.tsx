"use client";

import { ArrowUpIcon, XMarkIcon } from "@heroicons/react/20/solid";
import { ChangeEventHandler, useEffect, useRef, useState } from "react";

import { useSearchDispatch } from "@/components/search-provider";

export function SearchBar() {
  const dispatch = useSearchDispatch()!;

  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const sendButtonRef = useRef<HTMLButtonElement | null>(null);

  const [text, setText] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  const handleTextareaChange: ChangeEventHandler<HTMLTextAreaElement> = (
    event,
  ) => {
    setText(event.target.value);
  };

  const handleTextareaKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>,
  ) => {
    if (event.key === "Enter") {
      // Enter key
      event.preventDefault();
      if (sendButtonRef.current) {
        sendButtonRef.current.click(); // Trigger click event on send button
      }
    }
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"; // Reset height
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [text]);

  return (
    <div className="fixed bottom-0 flex w-full flex-col border-t bg-background/80 px-4 py-3 backdrop-blur">
      <div className="relative flex w-full items-center justify-center">
        <div className="flex w-full items-center gap-2 rounded-3xl bg-secondary px-3 py-1">
          <textarea
            ref={textareaRef}
            id="search-textarea"
            className="flex h-6 w-full resize-none rounded-md bg-transparent text-base outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="Search..."
            rows={1}
            value={text}
            onChange={handleTextareaChange}
            onKeyDown={handleTextareaKeyDown}
          />
        </div>
        <div className="w-10 shrink-0">
          {isSearching ? (
            <button
              ref={sendButtonRef!}
              className="absolute bottom-0.5 right-0 flex h-7 w-7 flex-none items-center justify-center rounded-full bg-destructive"
              onClick={() => {
                dispatch({ type: "vector_search", value: "" });
                setIsSearching(false);
                setText("");
              }}
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          ) : (
            <button
              ref={sendButtonRef!}
              disabled={text.length == 0}
              className="absolute bottom-0.5 right-0 flex h-7 w-7 flex-none items-center justify-center rounded-full bg-foreground text-background"
              onClick={() => {
                if (text.length) {
                  dispatch({ type: "vector_search", value: text });
                  setIsSearching(true);
                }
              }}
            >
              <ArrowUpIcon className="h-5 w-5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
