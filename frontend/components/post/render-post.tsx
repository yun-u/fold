import { ArxivPost } from "./post-arxiv";
import { TweetPost } from "./post-tweet";
import { WebPagePost } from "./post-webpage";

import { Post } from "@/lib/types";

export function renderPost(post: Post) {
  switch (post.category) {
    case "arxiv":
      return <ArxivPost post={post as ArxivPost} />;
    case "tweet":
      return <TweetPost post={post as TweetPost} />;
    case "webpage":
      return <WebPagePost post={post as WebPagePost} />;
    default:
      return null;
  }
}
