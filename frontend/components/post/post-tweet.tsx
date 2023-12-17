import { AtSymbolIcon } from "@heroicons/react/24/solid";
import { Tag } from "lucide-react";
import { Tweet } from "react-tweet";

import { AuthorBadge } from "./badge-author";
import { CategoryBadge } from "./badge-category";
import { addCommonProperties } from "./common-property";
import { Post } from "./post";
import { Property } from "./post-property";

import { XLogo } from "@/components/icons/x-logo";
import { Post as PostType } from "@/lib/types";

interface TweetPostMetadata extends Record<string, unknown> {
  user_id: string;
}

export interface TweetPost extends PostType {
  category: "tweet";
  metadata: TweetPostMetadata;
}

function getProperties(post: TweetPost): Property[] {
  return addCommonProperties(
    [
      {
        icon: <Tag className="h-3.5 w-3.5" />,
        name: "Category",
        content: (
          <CategoryBadge value={"tweet"}>
            <XLogo className="mr-1 h-3 w-3" />
            <div>Tweet</div>
          </CategoryBadge>
        ),
      },
      {
        icon: <AtSymbolIcon className="h-3.5 w-3.5" />,
        name: "User ID",
        content: (
          <AuthorBadge value={post.metadata.user_id}>
            @{post.metadata.user_id}
          </AuthorBadge>
        ),
      },
    ],
    post.created_at,
    post.url,
    post.score,
  );
}

export interface TweetPostProps {
  post: TweetPost;
}

export function TweetPost({ post }: TweetPostProps) {
  const getTweetId = (url: string) => {
    const parts = new URL(url).pathname.split("/");
    const tweetId = parts[parts.length - 1];
    return tweetId;
  };

  return (
    <Post
      documentId={post.document_id}
      properties={getProperties(post)}
      isRead={post.is_read}
      isBookmarked={post.is_bookmarked}
      links={post.links}
      backlinks={post.backlinks}
    >
      <div className="custom-tweet-theme mx-auto w-full max-w-[550px]">
        <Tweet id={getTweetId(post.url)} />
      </div>
    </Post>
  );
}
