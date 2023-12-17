import { cn } from "@/lib/utils";

type ScoreProps = React.HTMLAttributes<HTMLDivElement> & {
  value: number;
  max?: number;
};

export function Score({ className, value, max = 100 }: ScoreProps) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="font-mono text-sm leading-none text-muted-foreground">
        {value.toFixed(3)}
      </div>
      <div className="h-2 w-32 overflow-hidden rounded-lg bg-secondary">
        <div
          className="h-full overflow-hidden rounded-lg"
          style={{ width: ((value / max) * 100).toFixed(6) + "%" }}
        >
          <div className="h-full w-32 rounded-lg bg-gradient-to-r from-indigo-500 to-emerald-500" />
        </div>
      </div>
    </div>
  );
}
