import { XLogo } from "@/components/icons/x-logo";

export default function Page({ params }: { params: { slug: string } }) {
  return (
    <div className="">
      My Post: {params.slug}
      <div className="bg-pink-500">
        <XLogo className="mr-1 h-3 w-3" />
      </div>
    </div>
  );
}
