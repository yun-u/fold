import { Main } from "./main";

import { Header } from "@/components/header";
import { SearchFilter } from "@/components/search/search-filter";
import { Separator } from "@/components/ui/separator";

export default function Page({ params }: { params: { id: string } }) {
  return (
    <div>
      <Header>
        <Separator />
        <SearchFilter className="p-4" />
      </Header>
      <Main documentId={params.id} />
    </div>
  );
}
