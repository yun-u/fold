import { ExclamationTriangleIcon } from "@heroicons/react/24/solid";

export function Error({ message }: { message: string }) {
  return (
    <div className="flex h-full flex-col items-center justify-center">
      <div className="flex items-start gap-2 break-all leading-none text-red-500">
        <ExclamationTriangleIcon className="h-4 w-4 shrink-0" />
        <h2>{message}</h2>
      </div>
    </div>
  );
}
