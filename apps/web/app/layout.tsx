import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Certi — MoCRA 인증 자동화 플랫폼",
  description: "FDA MoCRA 시설 등록·제품 리스팅·컴플라이언스 자동화",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
            <Link href="/" className="flex items-center gap-2 font-bold text-brand-600">
              <span className="grid h-7 w-7 place-items-center rounded-md bg-brand-600 text-sm text-white">
                C
              </span>
              Certi
            </Link>
            <nav className="flex items-center gap-4 text-sm">
              <Link href="/diagnostics" className="text-slate-600 hover:text-brand-600">
                무료 진단
              </Link>
              <Link href="/dashboard" className="text-slate-600 hover:text-brand-600">
                대시보드
              </Link>
              <Link
                href="/login"
                className="rounded-md bg-brand-600 px-3 py-1.5 text-white hover:bg-brand-700"
              >
                로그인
              </Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
        <footer className="mt-16 border-t border-slate-200 py-6 text-center text-xs text-slate-400">
          Certi · MoCRA Compliance Automation · Draft
        </footer>
      </body>
    </html>
  );
}
