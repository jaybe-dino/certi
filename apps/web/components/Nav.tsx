"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearTokens, getAccessToken } from "@/lib/auth";

export default function Nav() {
  const router = useRouter();
  const pathname = usePathname();
  const [authed, setAuthed] = useState(false);

  // Re-check auth on every route change (login/logout navigations).
  useEffect(() => {
    setAuthed(!!getAccessToken());
  }, [pathname]);

  function logout() {
    clearTokens();
    setAuthed(false);
    router.push("/login");
  }

  return (
    <nav className="flex items-center gap-4 text-sm">
      <Link href="/diagnostics" className="text-slate-600 hover:text-brand-600">
        무료 진단
      </Link>
      {authed ? (
        <>
          <Link href="/dashboard" className="text-slate-600 hover:text-brand-600">
            대시보드
          </Link>
          <Link href="/intake" className="text-slate-600 hover:text-brand-600">
            접수 서류
          </Link>
          <Link href="/facilities" className="text-slate-600 hover:text-brand-600">
            시설
          </Link>
          <Link href="/products" className="text-slate-600 hover:text-brand-600">
            제품
          </Link>
          <button
            onClick={logout}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-slate-600 hover:bg-slate-100"
          >
            로그아웃
          </button>
        </>
      ) : (
        <Link
          href="/login"
          className="rounded-md bg-brand-600 px-3 py-1.5 text-white hover:bg-brand-700"
        >
          로그인
        </Link>
      )}
    </nav>
  );
}
