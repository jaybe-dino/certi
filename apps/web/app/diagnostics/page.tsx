"use client";

import { useState } from "react";
import { api, ApiError, API_BASE } from "@/lib/api";

type ChecklistItem = {
  key: string;
  title: string;
  required: boolean;
  form?: string | null;
  note?: string | null;
};

type DiagnosisResponse = {
  mandatory: boolean;
  exemption_status: string;
  summary: string;
  reasons: string[];
  checklist: ChecklistItem[];
  disclaimer: string;
};

const CATEGORIES = [
  { value: "general", label: "일반 (스킨케어/색조)" },
  { value: "eye_mucosa", label: "눈 점막 접촉 (아이라이너 등)" },
  { value: "injectable", label: "주사형" },
  { value: "internal_use", label: "체내 사용" },
  { value: "long_wear_24h", label: "24시간 초과 외형 변화" },
];

const SALES_TYPES = [
  { value: "own_brand_manufacturer", label: "자체 브랜드 제조" },
  { value: "contract_manufacturer", label: "OEM 수탁 제조" },
  { value: "importer", label: "수입·유통 (RP)" },
  { value: "distributor_only", label: "단순 판매" },
  { value: "foreign_to_us", label: "해외 → 미국 수출" },
];

export default function DiagnosticsPage() {
  const [revenue, setRevenue] = useState("");
  const [categories, setCategories] = useState<string[]>(["general"]);
  const [salesType, setSalesType] = useState("own_brand_manufacturer");
  const [result, setResult] = useState<DiagnosisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function toggleCategory(value: string) {
    setCategories((prev) =>
      prev.includes(value) ? prev.filter((c) => c !== value) : [...prev, value]
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    if (categories.length === 0) {
      setError("카테고리를 1개 이상 선택하세요.");
      return;
    }
    setLoading(true);
    try {
      const data = await api<DiagnosisResponse>("/diagnostics", {
        method: "POST",
        body: {
          annual_revenue_usd: Number(revenue) || 0,
          categories,
          sales_type: salesType,
        },
      });
      setResult(data);
    } catch (err) {
      // Show the real cause so misconfig (wrong API URL / CORS) is visible.
      const detail =
        err instanceof ApiError
          ? `[${err.status}] ${typeof err.detail === "string" ? err.detail : err.message}`
          : err instanceof Error
            ? `${err.name}: ${err.message}`
            : "알 수 없는 오류";
      setError(`요청 실패 · 호출 주소: ${API_BASE} · ${detail}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-8 lg:grid-cols-2">
      <section>
        <h1 className="text-2xl font-bold">무료 MoCRA 진단</h1>
        <p className="mt-2 text-sm text-slate-600">
          매출·카테고리·판매형태를 입력하면 의무/면제 여부와 체크리스트를 알려드립니다.
        </p>

        <form onSubmit={submit} className="mt-6 space-y-5 rounded-xl border border-slate-200 bg-white p-6">
          <div>
            <label className="block text-sm font-medium text-slate-700">
              최근 3년 평균 매출 (USD)
            </label>
            <input
              type="number"
              min={0}
              value={revenue}
              onChange={(e) => setRevenue(e.target.value)}
              placeholder="예: 500000"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-brand-500 focus:outline-none"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700">제품 카테고리</label>
            <div className="mt-2 space-y-2">
              {CATEGORIES.map((c) => (
                <label key={c.value} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={categories.includes(c.value)}
                    onChange={() => toggleCategory(c.value)}
                    className="h-4 w-4 rounded border-slate-300"
                  />
                  {c.label}
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700">판매 형태</label>
            <select
              value={salesType}
              onChange={(e) => setSalesType(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-brand-500 focus:outline-none"
            >
              {SALES_TYPES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-brand-600 px-4 py-2.5 font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {loading ? "진단 중..." : "진단하기"}
          </button>
          {error && <p className="text-sm text-red-600 break-all">{error}</p>}
          <p className="text-[11px] text-slate-400 break-all">API: {API_BASE}</p>
        </form>
      </section>

      <section>
        {result ? (
          <div className="rounded-xl border border-slate-200 bg-white p-6">
            <div
              className={`rounded-lg px-4 py-3 text-sm font-medium ${
                result.mandatory
                  ? "bg-amber-50 text-amber-800"
                  : "bg-green-50 text-green-800"
              }`}
            >
              {result.mandatory ? "⚠️ MoCRA 의무 대상" : "✅ 소규모 면제 가능성"}
            </div>
            <p className="mt-4 text-sm text-slate-700">{result.summary}</p>

            <ul className="mt-4 space-y-1 text-sm text-slate-600">
              {result.reasons.map((r, i) => (
                <li key={i} className="flex gap-2">
                  <span className="text-slate-400">•</span>
                  {r}
                </li>
              ))}
            </ul>

            <h3 className="mt-6 text-sm font-semibold text-slate-800">의무 체크리스트</h3>
            <div className="mt-2 space-y-2">
              {result.checklist.map((item) => (
                <div
                  key={item.key}
                  className="flex items-start justify-between rounded-lg bg-slate-50 px-3 py-2"
                >
                  <div>
                    <p className="text-sm font-medium text-slate-800">
                      {item.title}
                      {item.form && (
                        <span className="ml-2 rounded bg-slate-200 px-1.5 py-0.5 text-xs text-slate-600">
                          Form {item.form}
                        </span>
                      )}
                    </p>
                    {item.note && <p className="text-xs text-slate-500">{item.note}</p>}
                  </div>
                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${
                      item.required
                        ? "bg-brand-100 text-brand-700"
                        : "bg-slate-200 text-slate-500"
                    }`}
                  >
                    {item.required ? "필수" : "해당없음"}
                  </span>
                </div>
              ))}
            </div>

            <p className="mt-6 text-xs text-slate-400">{result.disclaimer}</p>
          </div>
        ) : (
          <div className="grid h-full place-items-center rounded-xl border border-dashed border-slate-300 bg-white/50 p-10 text-center text-sm text-slate-400">
            왼쪽 항목을 입력하고 진단하면
            <br />
            결과가 여기에 표시됩니다.
          </div>
        )}
      </section>
    </div>
  );
}
