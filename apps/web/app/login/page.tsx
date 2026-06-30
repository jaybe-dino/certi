"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import { saveTokens } from "@/lib/auth";

type TokenPair = { access_token: string; refresh_token: string };
type RegisterResponse = { tokens: TokenPair };

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [company, setCompany] = useState("");
  const [totp, setTotp] = useState("");
  const [needTotp, setNeedTotp] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "register") {
        const data = await api<RegisterResponse>("/auth/register", {
          method: "POST",
          body: { email, password, company_name: company },
        });
        saveTokens(data.tokens.access_token, data.tokens.refresh_token);
      } else {
        const data = await api<TokenPair>("/auth/login", {
          method: "POST",
          body: { email, password, totp_code: totp || null },
        });
        saveTokens(data.access_token, data.refresh_token);
      }
      router.push("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        if (typeof err.detail === "string" && err.detail.includes("TOTP")) {
          setNeedTotp(true);
        }
        setError(typeof err.detail === "string" ? err.detail : err.message);
      } else {
        setError("요청 중 오류가 발생했습니다.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <div className="mb-6 flex rounded-lg border border-slate-200 bg-white p-1 text-sm">
        {(["login", "register"] as const).map((m) => (
          <button
            key={m}
            onClick={() => {
              setMode(m);
              setError(null);
            }}
            className={`flex-1 rounded-md py-2 font-medium ${
              mode === m ? "bg-brand-600 text-white" : "text-slate-600"
            }`}
          >
            {m === "login" ? "로그인" : "회원가입"}
          </button>
        ))}
      </div>

      <form onSubmit={submit} className="space-y-4 rounded-xl border border-slate-200 bg-white p-6">
        {mode === "register" && (
          <div>
            <label className="block text-sm font-medium text-slate-700">회사명</label>
            <input
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-brand-500 focus:outline-none"
              required
            />
          </div>
        )}
        <div>
          <label className="block text-sm font-medium text-slate-700">이메일</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-brand-500 focus:outline-none"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">비밀번호</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={8}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-brand-500 focus:outline-none"
            required
          />
          {mode === "register" && (
            <p className="mt-1 text-xs text-slate-400">8자 이상</p>
          )}
        </div>
        {mode === "login" && needTotp && (
          <div>
            <label className="block text-sm font-medium text-slate-700">2FA 코드</label>
            <input
              value={totp}
              onChange={(e) => setTotp(e.target.value)}
              maxLength={6}
              placeholder="123456"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-brand-500 focus:outline-none"
            />
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-brand-600 px-4 py-2.5 font-medium text-white hover:bg-brand-700 disabled:opacity-50"
        >
          {loading ? "처리 중..." : mode === "login" ? "로그인" : "가입하기"}
        </button>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </form>
    </div>
  );
}
