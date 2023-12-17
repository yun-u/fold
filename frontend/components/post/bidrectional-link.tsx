import { ArrowTopRightOnSquareIcon } from "@heroicons/react/20/solid";
import { ArrowDownLeftIcon, ArrowUpRightIcon } from "@heroicons/react/24/solid";

import Link from "next/link";

import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { PostLink } from "@/lib/types";

type LinkPopoverProps = React.HTMLAttributes<HTMLDivElement> & {
  links: PostLink[];
};

function LinkPopover({ className, children, links }: LinkPopoverProps) {
  return (
    <div className={className}>
      <Popover>
        <PopoverTrigger>
          <div className="flex items-center gap-1 rounded-md px-2 py-1 text-sm font-semibold hover:bg-accent">
            {children}
          </div>
        </PopoverTrigger>
        <PopoverContent className="w-screen max-w-xl">
          <ul className="flex list-inside list-none flex-col gap-4 text-sm">
            {links.map((link, index) => (
              <li key={index} className="flex items-start gap-2">
                <ArrowTopRightOnSquareIcon className="h-3.5 w-3.5 shrink-0" />
                <Link
                  target="_blank"
                  href={`/${link.document_id}`}
                  className="break-all leading-none underline decoration-1 hover:decoration-2"
                >
                  {link.url}
                </Link>
              </li>
            ))}
          </ul>
        </PopoverContent>
      </Popover>
    </div>
  );
}

export interface BidrectionalLinkProps {
  links: PostLink[];
  backlinks: PostLink[];
}

export function BidrectionalLink({ links, backlinks }: BidrectionalLinkProps) {
  return links.length || backlinks.length ? (
    <div className="grid grid-cols-2">
      {links.length ? (
        <LinkPopover links={links} className="justify-self-start">
          <ArrowUpRightIcon className="h-3.5 w-3.5 shrink-0" />
          Link
        </LinkPopover>
      ) : (
        <div />
      )}
      {backlinks.length ? (
        <LinkPopover links={backlinks} className="justify-self-end">
          <ArrowDownLeftIcon className="h-3.5 w-3.5 shrink-0" />
          Backlink
        </LinkPopover>
      ) : (
        <div />
      )}
    </div>
  ) : null;
}
