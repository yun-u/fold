import { SearchParams } from "@/components/search-provider";
import { PostPage } from "@/lib/types";

function toURLSearchParams(params: Record<string, unknown>) {
  const results = [];

  for (const [key, value] of Object.entries(params)) {
    switch (typeof value) {
      case "string":
      case "number":
      case "bigint":
      case "boolean":
        value && results.push([key, value.toString()]);
        break;
      case "object":
        if (Array.isArray(value)) {
          results.push(...value.map((x) => [key, x]));
        }
        break;
    }
  }

  return new URLSearchParams(results);
}

export async function fetchPostList(
  searchParams: SearchParams,
  offset: number | undefined,
  count: number,
): Promise<PostPage> {
  try {
    const params = toURLSearchParams({
      ...searchParams,
      offset: offset,
      count: count,
    });

    const baseUrl = window.location.origin;
    const url = new URL(`/api/documents?${params}`, baseUrl);

    const response = await fetch(url);

    if (!response.ok) {
      // Check for non-successful HTTP status codes
      const errorMessage = await response.text(); // Extract the error message from the response body
      throw new Error(
        `HTTP error: Status: ${response.status}, Message: ${errorMessage}`,
      );
    }

    // await new Promise((r) => setTimeout(r, 1000));

    return await response.json(); // FIXME: `next_cursor` is `number | null`. Fix to `number | undefined`
  } catch (error) {
    console.error("Error:", error);
    throw error; // Re-throw the error if you want to handle it further up the call stack
  }
}
