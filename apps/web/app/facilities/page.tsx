"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useAuthToken, useWorkspaces } from "@/lib/hooks";
import WorkspacePicker from "@/components/WorkspacePicker";

type Facility = {
  id: string;
  name_en: string;
  address_en: string | null;
  email: string | null;
  fei: string | null;
  status: string;
};

const STATUS_STYLE: Record<string, string> = {
  draft: "bg-slate-100 text-slate-600",
  submitting: "bg-amber-100 text-amber-700",
  registered: "bg-green-100 text-green-700",
  renewal_due: "bg-amber-100 text-amber-700",
  expired: "bg-red-100 text-red-700",
};

const EMPTY = { name_en: "", address_en: "", email: "", fei: "" };

export default function FacilitiesPage() {
  const token = useAuthToken();
  const { workspaces, activeId, selectWorkspace } = useWorkspaces(token);
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [form, setForm] = useState({ ...EMPTY });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<Record<string, string>>({});

  const load = useCallback(async () => {
    if (!token || !activeId) return;
    try {
      const data = await api<Facility[]>(`/workspaces/${activeId}/facilities`, { token });
      setFacilities(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "목록을 불러오지 못했습니다.");
    }
  }, [token, activeId]);

  useEffect(() => {
    load();
  }, [load]);

  async function createFacility(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !activeId) return;
    setError(null);
    setBusy(true);
    try {
      await api(`/workspaces/${activeId}/facilities`, {
        method: "POST",
        token,
        body: {
          name_en: form.name_en,
          address_en: form.address_en || null,
          email: form.email || null,
          fei: form.fei || null,
        },
      });
      setForm({ ...EMPTY });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "생성 실패");
    } finally {
      setBusy(false);
    }
  }

  async function validate(id: string) {
    if (!token) return;
    const res = await api<{ valid: boolean; errors: string[] }>(
      `/facilities/${id}/validate`,
      { token }
    );
    setFeedback((f) => ({
      ...f,
      [id]: res.valid ? "✅ 검증 통과 — 제출 가능" : "⚠️ " + res.errors.join(" / "),
    }));
  }

  async function generateSpl(id: string) {
    if (!token) return;
    try {
      await api(`/facilities/${id}/generate-spl`, { method: "POST", token });
      setFeedback((f) => ({ ...f, [id]: "✅ SPL(5066) 생성 완료 — 제출 준비됨" }));
      await load();
    } catch (err) {
      const detail = err instanceof ApiError ? err.detail : null;
      const msg =
        detail && typeof detail === "object" && "errors" in detail
          ? (detail as { errors: string[] }).errors.join(" / ")
          : "SPL 생성 실패";
      setFeedback((f) => ({ ...f, [id]: "⚠️ " + msg }));
    }
  }

  async function markRegistered(id: string) {
    if (!token) return;
    const res = await api<{ renewal_due_date: string }>(
      `/facilities/${id}/mark-registered`,
      { method: "POST", token }
    );
    setFeedback((f) => ({
      ...f,
      [id]: `✅ 등록 완료 — 갱신 마감 ${res.renewal_due_date} 자동 생성`,
    }));
    await load();
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">시설 등록 (Form 5066)</h1>
        <p className="mt-1 text-sm text-slate-500">
          제조·가공 시설을 등록하고 SPL을 생성합니다.
        </p>
      </div>

      <WorkspacePicker workspaces={workspaces} activeId={activeId} onSelect={selectWorkspace} />

      {activeId && (
        <>
          <form
            onSubmit={createFacility}
            className="grid gap-3 rounded-xl border border-slate-200 bg-white p-5 sm:grid-cols-2"
          >
            <div className="sm:col-span-2 text-sm font-semibold text-slate-700">새 시설</div>
            <input
              placeholder="시설명 (영문) *"
              value={form.name_en}
              onChange={(e) => setForm({ ...form, name_en: e.target.value })}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
              required
            />
            <input
              placeholder="FEI 번호 (숫자 7~10자리)"
              value={form.fei}
              onChange={(e) => setForm({ ...form, fei: e.target.value })}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <input
              placeholder="주소 (영문)"
              value={form.address_en}
              onChange={(e) => setForm({ ...form, address_en: e.target.value })}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm sm:col-span-2"
            />
            <input
              placeholder="연락 이메일"
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm sm:col-span-2"
            />
            <button
              disabled={busy}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50 sm:col-span-2"
            >
              {busy ? "생성 중..." : "시설 추가"}
            </button>
            {error && <p className="text-sm text-red-600 sm:col-span-2">{error}</p>}
          </form>

          <div className="space-y-3">
            {facilities.length === 0 && (
              <p className="text-sm text-slate-400">등록된 시설이 없습니다.</p>
            )}
            {facilities.map((f) => (
              <div key={f.id} className="rounded-xl border border-slate-200 bg-white p-5">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold text-slate-900">{f.name_en}</p>
                    <p className="text-xs text-slate-500">
                      FEI: {f.fei || "—"} · {f.email || "이메일 없음"}
                    </p>
                    {f.address_en && (
                      <p className="text-xs text-slate-400">{f.address_en}</p>
                    )}
                  </div>
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      STATUS_STYLE[f.status] ?? "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {f.status}
                  </span>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button
                    onClick={() => validate(f.id)}
                    className="rounded-md border border-slate-300 px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100"
                  >
                    검증
                  </button>
                  <button
                    onClick={() => generateSpl(f.id)}
                    className="rounded-md border border-brand-300 bg-brand-50 px-3 py-1.5 text-xs text-brand-700 hover:bg-brand-100"
                  >
                    SPL 생성
                  </button>
                  {f.status !== "registered" && (
                    <button
                      onClick={() => markRegistered(f.id)}
                      className="rounded-md border border-green-300 bg-green-50 px-3 py-1.5 text-xs text-green-700 hover:bg-green-100"
                    >
                      등록 완료 처리
                    </button>
                  )}
                </div>
                {feedback[f.id] && (
                  <p className="mt-2 text-xs text-slate-600">{feedback[f.id]}</p>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
