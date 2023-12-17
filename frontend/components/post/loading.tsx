import { SpinnerDots } from "../icons/spinner-dots";

export function Loading() {
  return (
    <div className="flex h-12 items-center justify-center ">
      <SpinnerDots className="h-6 w-6 fill-foreground" />
    </div>
  );
}
