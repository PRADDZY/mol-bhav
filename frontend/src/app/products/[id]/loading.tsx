import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";

export default function Loading() {
  return (
    <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="grid gap-8 md:grid-cols-2">
        <Skeleton className="aspect-square w-full rounded-2xl" />

        <div className="flex flex-col justify-center">
          <Skeleton className="mb-3 h-6 w-20" />
          <Skeleton className="h-10 w-3/4" />
          <Skeleton className="mt-2 h-5 w-32" />
          <Skeleton className="mt-4 h-12 w-40" />
          <Skeleton className="mt-1 h-4 w-36" />

          <Separator className="my-6" />

          <div className="mb-6 space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
          </div>

          <div className="flex gap-3">
            <Skeleton className="h-12 flex-1" />
            <Skeleton className="h-12 flex-1" />
          </div>
        </div>
      </div>
    </main>
  );
}
