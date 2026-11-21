import { type QueryClient, queryOptions, useSuspenseQuery } from "@tanstack/react-query";
import { createRootRouteWithContext, Link, Outlet } from "@tanstack/react-router";
import { ProfileMenu } from "../components/ProfileMenu";
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
    <div className="flex min-h-screen flex-col bg-gray-50 text-gray-900 antialiased">
      <header className="sticky top-0 z-30 border-b border-gray-200 bg-white/90 backdrop-blur">
        <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
          <div className="flex items-center gap-8">
            <a href="/" className="flex items-center gap-2.5 font-semibold tracking-tight">
              <span className="logo-mark">{PROJECT_NAME.slice(0, 1).toUpperCase()}</span>
              <span>{PROJECT_NAME}</span>
            </a>
            <div className="hidden items-center gap-1 sm:flex">
              <a href="/" className="rounded-md px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900">
                Home
              </a>
              <Link
                to="/"
                activeOptions={{ exact: false }}
                className="rounded-md px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                activeProps={{ className: "bg-gray-100 text-gray-900" }}
              >
                Dashboard
              </Link>
              <a href="/settings/" className="rounded-md px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900">
                Settings
              </a>
            </div>
          </div>
          <ProfileMenu me={me} />
        </nav>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:px-6">
        <Outlet />
      </main>
    </div>
  );
}
