import { cn } from "@/lib/utils";

export function URLLink({
  className,
  href,
  ...props
}: React.HTMLProps<HTMLAnchorElement>) {
  return (
    <a
      href={href}
      target="_blank"
      className={cn(
        "break-all underline decoration-1 hover:decoration-2",
        className,
      )}
      {...props}
    >
      {href}
    </a>
  );
}
