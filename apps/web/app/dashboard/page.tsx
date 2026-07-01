"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { clearTokens, getAccessToken } from "@/lib/auth";

type Me = { email: string; role: string };
type Workspace = { id: string; brand_name: string };
type Task = {
  id: string;
  type: string;
  due_date: string;
  status: string;
  days_remaining: number;
};

const STATUS_STYLE: Record<string, string> = {
  scheduled: "bg-slate-100 text-slate-600",
  due_soon: "bg-amber-100 text-amber-700",
  overdue: "bg-red-100 text-red-700",
  done: "bg-green-100 text-green-700",
};

export default function DashboardPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [me, setMe] = useState<Me | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [active, setActive] = useState<Workspace | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [counts, setCounts] = useState({ facilities: 0, products: 0 });
  const [newBrand, setNewBrand] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const t = getAccessToken();
    if (!t) {
      router.replace("/login");
      return;
    }
    setToken(t);
  }, [router]);

  const loadWorkspaceData = useCallback(
    async (ws: Workspace, t: string) => {
      try {
        const [tasksData, facilities, products] = await Promise.all([
          api<Task[]>(`/workspaces/${ws.id}/compliance-tasks`, { token: t }),
          api<unknown[]>(`/workspaces/${ws.id}/facilities`, { token: t }),
          api<unknown[]>(`/workspaces/${ws.id}/products`, { token: t }),
        ]);
        setTasks(tasksData);
        setCounts({ facilities: facilities.length, products: products.length });
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "데이터 로드 실패");
      }
    },
    []
  );

  useEffect(() => {
    if (!token) return;
    (async () => {
      try {
        const [meData, ws] = await Promise.all([
          api<Me>("/auth/me", { token }),
          api<Workspace[]>("/workspaces", { token }),
        ]);
        setMe(meData);
        setWorkspaces(ws);
        if (ws.length > 0) {
          setActive(ws[0]);
          await loadWorkspaceData(ws[0], token);
        }
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          clearTokens();
          router.replace("/login");
        } else {
          setError("데이터 로드 실패");
        }
      }
    })();
  }, [token, router, loadWorkspaceData]);

  async function createWorkspace(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !newBrand.trim()) return;
    const ws = await api<Workspace>("/workspaces", {
      method: "POST",
      body: { brand_name: newBrand.trim() },
      token,
    });
    setWorkspaces((prev) => [...prev, ws]);
    setActive(ws);
    setNewBrand("");
    await loadWorkspaceData(ws, token);
  }

  function logout() {
    clearTokens();
    router.replace("/login");
  }

  if (!me) {
    return <p className="text-sm text-slate-500">불러오는 중...</p>;
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">대시보드</h1>
          <p className="text-sm text-slate-500">
            {me.email} · <span className="uppercase">{me.role}</span>
          </p>
        </div>
        <button
          onClick={logout}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100"
        >
          로그아웃
        </button>
      </div>

      {error && <p className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-600">{error}</p>}

      {/* Workspaces */}
      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-semibold text-slate-700">워크스페이스:</span>
          {workspaces.map((ws) => (
            <button
              key={ws.id}
              onClick={() => {
                setActive(ws);
                if (token) loadWorkspaceData(ws, token);
              }}
              className={`rounded-full px-3 py-1 text-sm ${
                active?.id === ws.id
                  ? "bg-brand-600 text-white"
                  : "bg-slate-100 text-slate-600"
              }`}
            >
              {ws.brand_name}
            </button>
          ))}
          {workspaces.length === 0 && (
            <span className="text-sm text-slate-400">아직 없음 — 아래에서 생성하세요.</span>
          )}
        </div>
        <form onSubmit={createWorkspace} className="mt-4 flex gap-2">
          <input
            value={newBrand}
            onChange={(e) => setNewBrand(e.target.value)}
            placeholder="새 브랜드명"
            className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
          />
          <button className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
            추가
          </button>
        </form>
      </section>

      {active && (
        <>
          <section className="grid gap-4 sm:grid-cols-3">
            {[
              ["시설", counts.facilities, "/facilities"],
              ["제품", counts.products, "/products"],
              ["임박/초과 마감", tasks.filter((t) => ["due_soon", "overdue"].includes(t.status)).length, null],
            ].map(([label, value, href]) => {
              const card = (
                <div className="h-full rounded-xl border border-slate-200 bg-white p-5 hover:border-brand-300">
                  <p className="text-sm text-slate-500">{label as string}</p>
                  <p className="mt-1 text-3xl font-bold text-slate-900">{value as number}</p>
                  {href && <p className="mt-1 text-xs text-brand-600">관리하기 →</p>}
                </div>
              );
              return href ? (
                <a key={label as string} href={href as string}>
                  {card}
                </a>
              ) : (
                <div key={label as string}>{card}</div>
              );
            })}
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="text-lg font-semibold">컴플라이언스 캘린더</h2>
            {tasks.length === 0 ? (
              <p className="mt-3 text-sm text-slate-400">등록된 마감 태스크가 없습니다.</p>
            ) : (
              <table className="mt-4 w-full text-sm">
                <thead className="text-left text-xs uppercase text-slate-400">
                  <tr>
                    <th className="pb-2">유형</th>
                    <th className="pb-2">마감일</th>
                    <th className="pb-2">D-day</th>
                    <th className="pb-2">상태</th>
                  </tr>
                </thead>
                <tbody>
                  {tasks.map((t) => (
                    <tr key={t.id} className="border-t border-slate-100">
                      <td className="py-2 text-slate-700">{t.type}</td>
                      <td className="py-2 text-slate-600">{t.due_date}</td>
                      <td className="py-2 text-slate-600">
                        {t.days_remaining < 0 ? `+${-t.days_remaining}d 초과` : `D-${t.days_remaining}`}
                      </td>
                      <td className="py-2">
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                            STATUS_STYLE[t.status] ?? "bg-slate-100 text-slate-600"
                          }`}
                        >
                          {t.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </>
      )}
    </div>
  );
}
