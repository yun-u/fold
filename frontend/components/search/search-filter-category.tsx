"use client";

import { Check, TagIcon } from "lucide-react";

import { useState } from "react";

import { SearchFilterButton } from "./search-filter-button";

import { useSearchDispatch, SearchParams } from "@/components/search-provider";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
  PopoverAnchor,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

const categories = [
  {
    value: "arxiv",
    label: "ArXiv",
  },
  {
    value: "tweet",
    label: "Tweet",
  },
  {
    value: "webpage",
    label: "WebPage",
  },
];

interface CategorySearchFilterProps {
  value: SearchParams["category"];
}

export function CategorySearchFilter({ value }: CategorySearchFilterProps) {
  const dispatch = useSearchDispatch()!;

  const [open, setOpen] = useState(false);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <SearchFilterButton
          role="combobox"
          aria-expanded={open}
          enabled={value.length > 0}
          className="relative"
        >
          <TagIcon className="mr-1 h-3 w-3" />
          Category
          {value.length > 0 &&
            ": " +
              categories
                .filter((category) => value.includes(category.value))
                .map((category) => category.label)
                .join(", ")}
          <PopoverAnchor asChild>
            <div className="absolute bottom-0 left-1/2"></div>
          </PopoverAnchor>
        </SearchFilterButton>
      </PopoverTrigger>
      <PopoverContent className="w-[16rem] border p-0">
        <Command>
          <CommandInput placeholder="Search category..." />
          <CommandEmpty>No category found.</CommandEmpty>
          <CommandGroup>
            {categories.map((category) => (
              <CommandItem
                key={category.value}
                onSelect={(currentValue) => {
                  if (value.includes(currentValue)) {
                    const newValues = value.filter((x) => currentValue != x);
                    dispatch({ type: "category", value: newValues });
                  } else {
                    dispatch({
                      type: "category",
                      value: [...value, currentValue],
                    });
                  }
                }}
              >
                <Check
                  className={cn(
                    "mr-2 h-4 w-4",
                    value.includes(category.value)
                      ? "opacity-100"
                      : "opacity-0",
                  )}
                />
                {category.label}
              </CommandItem>
            ))}
          </CommandGroup>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
