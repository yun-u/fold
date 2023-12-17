import { useSearchDispatch } from "@/components/search-provider";
import { Badge } from "@/components/ui/badge";

type CategoryProps = React.HTMLAttributes<HTMLDivElement> & { value: string };

export function CategoryBadge({ children, value }: CategoryProps) {
  const dispatch = useSearchDispatch()!;

  return (
    <Badge
      className="shrink-0 cursor-pointer py-px"
      onClick={() => dispatch({ type: "category", value: [value] })}
    >
      {children}
    </Badge>
  );
}
