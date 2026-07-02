"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useAuthToken, useWorkspaces } from "@/lib/hooks";
import WorkspacePicker from "@/components/WorkspacePicker";

type ChecklistItem = {
  type: string;
  title: string;
  required: boolean;
  uploaded: boolean;
  latest_file_url: string | null;
};

type Checklist = { complete: boolean; items: ChecklistItem[] };

export default function IntakePage() {
  const token = useAuthToken();
  const { workspaces, activeId, selectWorkspace } = useWorkspaces(token);
  const [checklist, setChecklist] = useState<Checklist | null>(null);
  const [urls, setUrls] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token || !activeId) return;
    try {
      const data = await api<Checklist>(
        `/workspaces/${activeId}/intake-checklist`,
        { token }
      );
      setChecklist(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "체크리스트를 불러오지 못했습니다.");
    }
  }, [token, activeId]);

  useEffect(() => {
    load();
  }, [load]);

  async function upload(type: string) {
    if (!token || !activeId) return;
    const url = (urls[type] || "").trim();
    if (!url) return;
    setError(null);
    try {
      await api(`/workspaces/${activeId}/documents`, {
        method: "POST",
        token,
        body: { owner_ref: "company", type, file_url: url },
      });
      setUrls((u) => ({ ...u, [type]: "" }));
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "등록 실패");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">접수 서류 체크리스트</h1>
        <p className="mt-1 text-sm text-slate-500">
          대행 접수에 필요한 회사 서류를 업로드(문서 URL 등록)합니다.
        </p>
      </div>

      <WorkspacePicker workspaces={workspaces} activeId={activeId} onSelect={selectWorkspace} />

      {error && <p className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-600">{error}</p>}

      {activeId && checklist && (
        <>
          <div
            className={`rounded-lg px-4 py-3 text-sm font-medium ${
              checklist.complete
                ? "bg-green-50 text-green-800"
                : "bg-amber-50 text-amber-800"
            }`}
          >
            {checklist.complete
              ? "✅ 필수 서류가 모두 접수되었습니다."
              : "⚠️ 아직 접수되지 않은 필수 서류가 있습니다."}
          </div>

          <div className="space-y-3">
            {checklist.items.map((item) => (
              <div
                key={item.type}
                className="rounded-xl border border-slate-200 bg-white p-5"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-slate-900">
                      {item.title}
                      {item.required && <span className="ml-1 text-red-500">*</span>}
                    </p>
                    {item.latest_file_url && (
                      <a
                        href={item.latest_file_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-brand-600 underline"
                      >
                        {item.latest_file_url}
                      </a>
                    )}
                  </div>
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      item.uploaded
                        ? "bg-green-100 text-green-700"
                        : "bg-slate-100 text-slate-500"
                    }`}
                  >
                    {item.uploaded ? "접수됨" : "미접수"}
                  </span>
                </div>
                <div className="mt-3 flex gap-2">
                  <input
                    placeholder="문서 URL (S3/드라이브 링크 등)"
                    value={urls[item.type] || ""}
                    onChange={(e) =>
                      setUrls((u) => ({ ...u, [item.type]: e.target.value }))
                    }
                    className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                  <button
                    onClick={() => upload(item.type)}
                    className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
                  >
                    {item.uploaded ? "교체" : "등록"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
