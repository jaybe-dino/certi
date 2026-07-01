"use client";

import type { Workspace } from "@/lib/hooks";

export default function WorkspacePicker({
  workspaces,
  activeId,
  onSelect,
}: {
  workspaces: Workspace[];
  activeId: string | null;
  onSelect: (id: string) => void;
}) {
  if (workspaces.length === 0) {
    return (
      <p className="rounded-lg bg-amber-50 px-4 py-2 text-sm text-amber-700">
        먼저 <a href="/dashboard" className="underline">대시보드</a>에서 워크스페이스를 만들어 주세요.
      </p>
    );
  }
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-sm font-medium text-slate-500">워크스페이스:</span>
      {workspaces.map((ws) => (
        <button
          key={ws.id}
          onClick={() => onSelect(ws.id)}
          className={`rounded-full px-3 py-1 text-sm ${
            activeId === ws.id ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-600"
          }`}
        >
          {ws.brand_name}
        </button>
      ))}
    </div>
  );
}
