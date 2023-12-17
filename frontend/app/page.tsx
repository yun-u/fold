import { Header } from "@/components/header";
import { PostList } from "@/components/post";
import { SearchFilter } from "@/components/search/search-filter";
import { SearchBar } from "@/components/search/searchbar";
import { Separator } from "@/components/ui/separator";

export default async function Page() {
  return (
    <div>
      <Header>
        <Separator />
        <SearchFilter />
      </Header>
      <PostList className="mt-28" count={10} />
      <SearchBar />
    </div>
  );
}
