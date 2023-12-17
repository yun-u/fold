import { Users2, CalendarDays, Tag } from "lucide-react";

import { AuthorBadge } from "./badge-author";
import { CategoryBadge } from "./badge-category";
import { addCommonProperties } from "./common-property";
import { Post } from "./post";
import { Property } from "./post-property";
import { toLocaleString } from "./utils";

import { ArxivLogo } from "@/components/icons/arxiv-logo";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Post as PostType } from "@/lib/types";

interface ArxivPostMetadata extends Record<string, unknown> {
  authors: string[];
  published: string;
  summary: string;
  title: string;
}

export interface ArxivPost extends PostType {
  category: "arxiv";
  metadata: ArxivPostMetadata;
}

function getProperties(post: ArxivPost): Property[] {
  return addCommonProperties(
    [
      {
        icon: <Tag className="h-3.5 w-3.5" />,
        name: "Category",
        content: (
          <CategoryBadge value="arxiv">
            <ArxivLogo className="mr-1 h-3 w-3" />
            ArXiv
          </CategoryBadge>
        ),
      },
      {
        icon: <CalendarDays className="h-3.5 w-3.5" />,
        name: "Published",
        content: toLocaleString(post.metadata.published),
      },
      {
        icon: <Users2 className="h-3.5 w-3.5" />,
        name: "Authors",
        content: (
          <div className="flex flex-wrap gap-1">
            {post.metadata.authors.map((author, index) => (
              <AuthorBadge key={index} value={author}>
                {author}
              </AuthorBadge>
            ))}
          </div>
        ),
      },
    ],
    post.created_at,
    post.url,
    post.score,
  );
}

export interface ArxivPostProps {
  post: ArxivPost;
}

export function ArxivPost({ post }: ArxivPostProps) {
  return (
    <Post
      documentId={post.document_id}
      properties={getProperties(post)}
      title={post.metadata.title}
      isRead={post.is_read}
      isBookmarked={post.is_bookmarked}
      links={post.links}
      backlinks={post.backlinks}
    >
      <Accordion type="single" collapsible className="w-full">
        <AccordionItem value="item-1" className="border-0">
          <AccordionTrigger>Summary</AccordionTrigger>
          <AccordionContent>
            <p className="font-serif tracking-wide">{post.metadata.summary}</p>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </Post>
  );
}
