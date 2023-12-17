import { XCircleIcon } from "@heroicons/react/24/solid";

import { cn } from "@/lib/utils";

export function ErrorCallout({
  children,
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "flex w-full min-w-fit flex-wrap items-start gap-2 break-all rounded-md border border-red-400 bg-red-200/50 px-2 py-1 font-mono text-base leading-none text-red-400 dark:bg-red-900/50",
        className,
      )}
      {...props}
    >
      <XCircleIcon className="h-4 w-4 shrink-0" />
      {children}
    </div>
  );
}
