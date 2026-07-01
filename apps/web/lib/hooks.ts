"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { clearTokens, getAccessToken } from "@/lib/auth";

/** Redirect to /login when no token is present; returns the current token. */
export function useAuthToken(): string | null {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const t = getAccessToken();
    if (!t) {
      router.replace("/login");
      return;
    }
    setToken(t);
  }, [router]);

  return token;
}

export type Workspace = { id: string; brand_name: string };

const ACTIVE_WS_KEY = "certi_active_ws";

/**
 * Loads the org's workspaces and tracks a selected one (persisted in
 * localStorage so it stays consistent across pages).
 */
export function useWorkspaces(token: string | null) {
  const router = useRouter();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    (async () => {
      try {
        const ws = await api<Workspace[]>("/workspaces", { token });
        setWorkspaces(ws);
        const stored = typeof window !== "undefined" ? localStorage.getItem(ACTIVE_WS_KEY) : null;
        const pick = ws.find((w) => w.id === stored) ?? ws[0];
        if (pick) setActiveId(pick.id);
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          clearTokens();
          router.replace("/login");
        }
      } finally {
        setLoading(false);
      }
    })();
  }, [token, router]);

  function selectWorkspace(id: string) {
    setActiveId(id);
    if (typeof window !== "undefined") localStorage.setItem(ACTIVE_WS_KEY, id);
  }

  const active = workspaces.find((w) => w.id === activeId) ?? null;
  return { workspaces, active, activeId, selectWorkspace, loading, setWorkspaces };
}
