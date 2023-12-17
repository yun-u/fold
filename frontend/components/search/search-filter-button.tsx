import { ChevronDownIcon } from "@heroicons/react/20/solid";

import { forwardRef } from "react";

import { cn } from "@/lib/utils";

interface SearchFilterButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  enabled?: boolean;
}

const SearchFilterButton = forwardRef<
  HTMLButtonElement,
  SearchFilterButtonProps
>(({ className, children, enabled, disabled, ...props }, ref) => {
  return (
    <button
      className={cn(
        "inline-flex h-6 shrink-0 items-center justify-between rounded-full border bg-background px-2 py-0 text-sm ring-offset-background transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
        enabled || disabled
          ? "border-transparent bg-foreground text-background"
          : "",
        className,
      )}
      disabled={disabled}
      ref={ref}
      {...props}
    >
      {children}
      <ChevronDownIcon className="ml-1 h-3 w-3" />
    </button>
  );
});
SearchFilterButton.displayName = "SearchFilterButton";

export { SearchFilterButton };
