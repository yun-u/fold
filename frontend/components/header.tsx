import { RootLink } from "./root-link";

import { ThemeSwitch } from "@/components/theme-switch";

export function Header({ children }: { children?: React.ReactNode }) {
  return (
    <div className="fixed top-0 z-40 w-full border-b bg-background/80 backdrop-blur transition-colors">
      <div className="px-4 py-2 lg:px-8">
        <div className="flex items-center">
          <RootLink />
          <ThemeSwitch className="ml-auto" />
        </div>
      </div>
      {children}
    </div>
  );
}
