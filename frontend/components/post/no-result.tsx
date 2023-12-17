import { MagnifyingGlassIcon } from "@heroicons/react/24/solid";

export function NoResult() {
  return (
    <div className="flex h-full min-h-[8rem] flex-col items-center justify-center">
      <div className="flex items-center gap-2">
        <MagnifyingGlassIcon className="h-4 w-4 shrink-0" />
        <h2>No Result</h2>
      </div>
    </div>
  );
}
