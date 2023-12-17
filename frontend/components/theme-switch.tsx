"use client";

import { MoonIcon, SunIcon } from "@heroicons/react/24/solid";
import { useTheme } from "next-themes";
import * as React from "react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function ThemeSwitch({
  className,
}: React.HTMLAttributes<HTMLDivElement>) {
  const { setTheme } = useTheme();

  return (
    <div className={className}>
      <DropdownMenu modal={false}>
        <DropdownMenuTrigger asChild>
          <Button
            className="hover:bg-zinc-100 dark:hover:bg-zinc-800"
            variant="ghost"
            size="icon"
          >
            <SunIcon className="block h-6 w-6 dark:hidden" />
            <MoonIcon className="hidden h-6 w-6 dark:block" />
            <span className="sr-only">Toggle theme</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem
            onClick={() => setTheme("light")}
            className="focus:bg-zinc-100 dark:focus:bg-zinc-800"
          >
            Light
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() => setTheme("dark")}
            className="focus:bg-zinc-100 dark:focus:bg-zinc-800"
          >
            Dark
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() => setTheme("system")}
            className="focus:bg-zinc-100 dark:focus:bg-zinc-800"
          >
            System
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
