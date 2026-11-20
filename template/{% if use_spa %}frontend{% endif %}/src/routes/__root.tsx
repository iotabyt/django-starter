import { type QueryClient, queryOptions, useSuspenseQuery } from "@tanstack/react-query";
import { createRootRouteWithContext, Link, Outlet } from "@tanstack/react-router";
import { get } from "../lib/api";
import { PROJECT_NAME } from "../lib/config";
import type { Me } from "../lib/types";

export const meQuery = queryOptions({
  queryKey: ["me"],
  queryFn: () => get<Me>("/me"),
});

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  loader: ({ context }) => context.queryClient.ensureQueryData(meQuery),
  component: RootLayout,
});

function RootLayout() {
  const { data: me } = useSuspenseQuery(meQuery);

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 antialiased">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3">
          <Link to="/" className="font-semibold tracking-tight">
            {PROJECT_NAME}
          </Link>
          <nav className="flex items-center gap-4 text-sm">
            <span className="hidden text-gray-600 sm:inline">{me.email}</span>
            {/* Account pages are server-rendered by allauth. */}
            <a href="/accounts/email/" className="font-medium text-indigo-600 hover:underline">
              Account
            </a>
            <a href="/accounts/logout/" className="font-medium text-indigo-600 hover:underline">
              Sign out
            </a>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
