import { Tag, Globe, User2 } from "lucide-react";

import { CategoryBadge } from "./badge-category";
import { addCommonProperties } from "./common-property";
import { Post } from "./post";
import { Property } from "./post-property";

import { EmbedCard } from "@/components/embed-card";
import { Post as PostType } from "@/lib/types";

interface WebPagePostMetadata extends Record<string, unknown> {
  author: string;
  description: string;
  image: string;
  logo: string;
  title: string;
}

export interface WebPagePost extends PostType {
  category: "webpage";
  metadata: WebPagePostMetadata;
}

function getProperties(post: WebPagePost): Property[] {
  const properties: Property[] = [
    {
      icon: <Tag className="h-3.5 w-3.5" />,
      name: "Category",
      content: (
        <CategoryBadge value={"webpage"}>
          <Globe className="mr-1 flex h-3 w-3" />
          WebPage
        </CategoryBadge>
      ),
    },
  ];

  if (post.metadata.author) {
    properties.push({
      icon: <User2 className="h-3.5 w-3.5" />,
      name: "Author",
      content: <span className="break-all">{post.metadata.author}</span>,
    });
  }

  return addCommonProperties(properties, post.created_at, post.url, post.score);
}

export interface WebPagePostProps {
  post: WebPagePost;
}

export function WebPagePost({ post }: WebPagePostProps) {
  return (
    <Post
      documentId={post.document_id}
      properties={getProperties(post)}
      isRead={post.is_read}
      isBookmarked={post.is_bookmarked}
      links={post.links}
      backlinks={post.backlinks}
    >
      <EmbedCard
        description={post.metadata.description}
        image={post.metadata.image}
        logo={post.metadata.logo}
        title={post.metadata.title}
        url={post.url}
      />
    </Post>
  );
}
