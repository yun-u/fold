/* eslint-disable @next/next/no-img-element */

import { cn } from "@/lib/utils";

type EmbedCardProps = React.HTMLProps<HTMLDivElement> & {
  description: string;
  image?: string;
  logo?: string;
  title: string;
  url: string;
};

export function EmbedCard({ className, url, image, ...props }: EmbedCardProps) {
  return (
    <div
      className={cn(
        "box-border flex h-[6.625rem] w-full max-w-[550px] justify-center",
        className,
      )}
    >
      <a
        href={url}
        target="_blank"
        className="flex w-[36rem] overflow-hidden rounded-md border transition-colors hover:bg-accent"
      >
        <EmbedCardContent url={url} {...props} />
        {image && <EmbedCardThumbnail src={image} />}
      </a>
    </div>
  );
}

type EmbedContentProps = {
  description: string;
  logo?: string;
  title: string;
  url: string;
};

function EmbedCardContent({
  description,
  logo,
  title,
  url,
}: EmbedContentProps) {
  return (
    <div className="flex h-full w-1 flex-1 flex-col gap-1 p-3">
      <div className="h-6 truncate text-sm">{title}</div>
      <div className="h-8 overflow-hidden text-xs text-muted-foreground">
        {description}
      </div>
      <div className="flex h-4 items-center text-xs">
        <div className="shrink-0">
          {logo && <EmbedCardLogo src={logo} className="mr-1 h-4 w-4" />}
        </div>
        <div className="truncate">{url}</div>
      </div>
    </div>
  );
}

function EmbedCardLogo({
  className,
  src,
  ...props
}: React.HTMLProps<HTMLImageElement>) {
  return <img src={src} alt="Logo" className={className} {...props} />;
}

function EmbedCardThumbnail({ src }: React.HTMLProps<HTMLImageElement>) {
  // FIXME: img src 404
  return (
    <div className="relative hidden h-[6.625rem] w-[13.25rem] flex-none md:block">
      <div className="absolute -right-px -top-px h-full w-full">
        <img
          src={src}
          alt="Thumbnail"
          className="h-full w-full rounded-r-md object-cover"
        />
      </div>
    </div>
  );
}
