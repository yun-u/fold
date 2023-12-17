"use client";

import { Text } from "lucide-react";

import { useState } from "react";

import { SearchFilterButton } from "./search-filter-button";

import { TextInput } from "./text-input";

import { useSearchDispatch, SearchParams } from "@/components/search-provider";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
  PopoverAnchor,
} from "@/components/ui/popover";

interface TextSerachFilterProps {
  value: SearchParams["text"];
}

export function TextSerachFilter({ value }: TextSerachFilterProps) {
  const dispatch = useSearchDispatch()!;

  const [open, setOpen] = useState(false);

  const handleInputValueChange = (value: string) => {
    dispatch({ type: "text", value: value });
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
          <Text className="mr-1 h-3 w-3" />
          Text
          {value && ": " + value}
          <PopoverAnchor asChild>
            <div className="absolute bottom-0 left-1/2"></div>
          </PopoverAnchor>
        </SearchFilterButton>
      </PopoverTrigger>
      <PopoverContent className="w-[16rem] border p-3">
        <TextInput
          placeholder="Type a value..."
          value={value}
          onInputValueChange={handleInputValueChange}
        />
      </PopoverContent>
    </Popover>
  );
}
