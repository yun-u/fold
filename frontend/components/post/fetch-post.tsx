import { Post } from "@/lib/types";

export async function fetchPost(documentId: string): Promise<{ data: Post[] }> {
  const baseUrl = window.location.origin;
  const url = new URL(`/api/document?id=${documentId}`, baseUrl);

  try {
    const response = await fetch(url);

    if (!response.ok) {
      // Check for non-successful HTTP status codes
      const errorMessage = await response.text(); // Extract the error message from the response body
      throw new Error(
        `HTTP error: Status: ${response.status}, Message: ${errorMessage}`,
      );
    }

    return await response.json();
  } catch (error) {
    console.error("Error:", error);
    throw error; // Re-throw the error if you want to handle it further up the call stack
  }
}
