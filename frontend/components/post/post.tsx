import { Actions } from "./actions";
import { BidrectionalLink, BidrectionalLinkProps } from "./bidrectional-link";
import { Property } from "./post-property";

import { Separator } from "@/components/ui/separator";

interface PostProps
  extends React.ComponentProps<"div">,
    BidrectionalLinkProps,
    Actions {
  properties: Property[];
  title?: string;
}

export function Post({
  documentId,
  properties,
  title,
  isRead,
  isBookmarked,
  links,
  backlinks,
  children,
}: PostProps) {
  return (
    <>
      <Separator />
      <div className="mx-auto max-w-[550px]">
        <Actions
          documentId={documentId}
          isRead={isRead}
          isBookmarked={isBookmarked}
        />
        <div className="flex flex-col gap-4 p-4">
          {title ? <h3 className="text-xl font-semibold">{title}</h3> : null}
          <Property properties={properties} />
          <BidrectionalLink links={links} backlinks={backlinks} />
          <div className="flex flex-col items-center">{children}</div>
        </div>
      </div>
    </>
  );
}
