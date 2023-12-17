"use client";

import { User2 } from "lucide-react";
import * as React from "react";

import { SearchFilterButton } from "./search-filter-button";

import { TextInput } from "./text-input";

import { useSearchDispatch, SearchParams } from "@/components/search-provider";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
  PopoverAnchor,
} from "@/components/ui/popover";

interface AuthorSearchFilterProps {
  value: SearchParams["author"];
}

export function AuthorSearchFilter({ value }: AuthorSearchFilterProps) {
  const dispatch = useSearchDispatch()!;

  const [open, setOpen] = React.useState(false);

  const handleInputValueChange = (value: string) => {
    dispatch({ type: "author", value: value });
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <SearchFilterButton
          role="combobox"
          aria-expanded={open}
          enabled={!!value}
          className="relative"
        >
          <User2 className="mr-1 h-3 w-3" />
          Author
          {value && ": " + value}
          <PopoverAnchor asChild>
            <div className="absolute bottom-0 left-1/2"></div>
          </PopoverAnchor>
        </SearchFilterButton>
      </PopoverTrigger>
      <PopoverContent className="w-[16rem] border-border p-3">
        <TextInput
          placeholder="Type a value..."
          value={value}
          onInputValueChange={handleInputValueChange}
        />
      </PopoverContent>
    </Popover>
  );
}
