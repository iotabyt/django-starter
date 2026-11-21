import { useEffect, useRef, useState } from "react";
import { getCookie } from "../lib/api";
import type { Me } from "../lib/types";
import { Avatar, Icon, type IconName } from "./ui";

// Account pages are server-rendered (Django + allauth); these are plain links to them.
const links: { href: string; label: string; icon: IconName }[] = [
  { href: "/settings/", label: "Profile", icon: "user" },
  { href: "/accounts/email/", label: "Email addresses", icon: "envelope" },
  { href: "/accounts/password/change/", label: "Password", icon: "key" },
  { href: "/accounts/2fa/", label: "Two-factor authentication", icon: "shield" },
];

export function ProfileMenu({ me }: { me: Me }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onClick = (event: MouseEvent) => {
      if (!ref.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-label="Account menu"
        className="flex cursor-pointer items-center gap-1.5 rounded-full p-0.5 pr-1.5 hover:bg-gray-100"
      >
        <Avatar name={me.name} email={me.email} />
        <Icon name="chevronDown" className="size-4 text-gray-500" />
      </button>
      {open && (
        <div className="absolute right-0 z-40 mt-2 w-64 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-lg ring-1 ring-black/5">
          <div className="flex items-center gap-3 border-b border-gray-100 px-4 py-3">
            <Avatar name={me.name} email={me.email} />
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-gray-900">{me.name || "Your account"}</p>
              <p className="truncate text-sm text-gray-500">{me.email}</p>
            </div>
          </div>
          <div className="py-1">
            {links.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-gray-900"
              >
                <Icon name={link.icon} className="size-4 text-gray-400" />
                {link.label}
              </a>
            ))}
            {me.admin_url && (
              <a
                href={me.admin_url}
                className="flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 hover:text-gray-900"
              >
                <Icon name="lock" className="size-4 text-gray-400" />
                Admin
              </a>
            )}
          </div>
          <form method="post" action="/accounts/logout/" className="border-t border-gray-100 py-1">
            <input type="hidden" name="csrfmiddlewaretoken" value={getCookie("csrftoken") ?? ""} />
            <button
              type="submit"
              className="flex w-full cursor-pointer items-center gap-3 px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 hover:text-gray-900"
            >
              <Icon name="signOut" className="size-4 text-gray-400" />
              Sign out
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
