import { useSearchDispatch } from "@/components/search-provider";
import { Badge } from "@/components/ui/badge";

type AuthorProps = React.HTMLAttributes<HTMLDivElement> & { value: string };

export function AuthorBadge({ children, value }: AuthorProps) {
  const dispatch = useSearchDispatch()!;

  return (
    <Badge
      className="shrink-0 cursor-pointer py-px"
      onClick={() => dispatch({ type: "author", value: value })}
    >
      {children}
    </Badge>
  );
}
