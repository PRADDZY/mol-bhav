import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";

export default function Loading() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Hero skeleton */}
      <section className="mb-10 text-center">
        <Skeleton className="mx-auto mb-4 h-16 w-16 rounded-2xl" />
        <Skeleton className="mx-auto h-10 w-56" />
        <Skeleton className="mx-auto mt-3 h-6 w-80" />
      </section>

      {/* Grid skeleton */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i} className="h-full">
            <Skeleton className="h-44 w-full rounded-t-xl" />
            <CardHeader className="pb-2">
              <Skeleton className="h-5 w-3/4" />
            </CardHeader>
            <CardContent className="pb-2">
              <Skeleton className="h-8 w-28" />
              <Skeleton className="mt-2 h-4 w-20" />
            </CardContent>
            <CardFooter>
              <Skeleton className="h-9 w-full" />
            </CardFooter>
          </Card>
        ))}
      </div>
    </main>
  );
}
