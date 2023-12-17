"use client";

import Image from "next/image";
import Link from "next/link";

import { useSearchDispatch } from "@/components/search-provider";

export function RootLink() {
  const dispatch = useSearchDispatch()!;

  return (
    <Link
      href="/"
      onClick={() => dispatch({ type: "vector_search_document", value: "" })}
    >
      <Image
        src="/logo.svg"
        alt="Logo"
        className="dark:invert"
        width={24}
        height={24}
        priority
        draggable={false}
      />
    </Link>
  );
}
