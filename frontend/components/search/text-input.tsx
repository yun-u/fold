"use client";

import { XCircleIcon } from "@heroicons/react/20/solid";

import { useRef, useState } from "react";

import { cn } from "@/lib/utils";

interface TextInputProps extends React.HTMLProps<HTMLDivElement> {
  onInputValueChange?: (value: string) => void;
  placeholder: string;
  value: string;
}

export function TextInput({
  className,
  placeholder,
  value = "",
  onInputValueChange,
  ...props
}: TextInputProps) {
  const [inputValue, setInputValue] = useState(value);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.value;
    setInputValue(newValue);
    if (onInputValueChange) {
      onInputValueChange(newValue);
    }
  };

  const handleResetClick = () => {
    setInputValue("");
    if (onInputValueChange) {
      onInputValueChange("");
    }
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  return (
    <div
      className={cn(
        "dark:focus-visible:ring-wihte flex w-full items-center rounded-md bg-secondary px-1.5 py-1 ring-offset-background focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        className,
      )}
      {...props}
    >
      <input
        ref={inputRef}
        type="text"
        className="w-full bg-secondary text-sm outline-none placeholder:text-muted-foreground"
        placeholder={placeholder}
        value={inputValue}
        onChange={handleInputChange}
      />
      {inputValue && (
        <div
          className="ml-1 shrink-0 select-none"
          tabIndex={0}
          role="button"
          onClick={handleResetClick}
        >
          <XCircleIcon className="h-4 w-4 text-muted-foreground hover:opacity-80" />
        </div>
      )}
    </div>
  );
}
