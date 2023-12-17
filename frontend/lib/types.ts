export interface PostLink {
  document_id: string;
  url: string;
}

export interface Post {
  category: string;
  created_at: string;
  document_id: string;
  metadata: Record<string, unknown>;
  score?: number;
  url: string;
  is_read: boolean;
  is_bookmarked: boolean;
  links: PostLink[];
  backlinks: PostLink[];
}

export interface PostPage {
  data: Post[];
  next_cursor?: number;
}
