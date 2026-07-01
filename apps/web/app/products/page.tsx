"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useAuthToken, useWorkspaces } from "@/lib/hooks";
import WorkspacePicker from "@/components/WorkspacePicker";

type Product = { id: string; name: string; category: string | null; status: string };
type Ingredient = {
  id: string;
  raw_name: string;
  inci_name: string | null;
  confidence: string | null;
  flag: boolean;
};
type Facility = { id: string; name_en: string; fei: string | null };

const CONF_STYLE: Record<string, string> = {
  high: "bg-green-100 text-green-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-red-100 text-red-700",
};

export default function ProductsPage() {
  const token = useAuthToken();
  const { workspaces, activeId, selectWorkspace } = useWorkspaces(token);
  const [products, setProducts] = useState<Product[]>([]);
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [selected, setSelected] = useState<Product | null>(null);
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [newProduct, setNewProduct] = useState({ name: "", category: "" });
  const [rawNames, setRawNames] = useState("");
  const [linkFacility, setLinkFacility] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadProducts = useCallback(async () => {
    if (!token || !activeId) return;
    const [prods, facs] = await Promise.all([
      api<Product[]>(`/workspaces/${activeId}/products`, { token }),
      api<Facility[]>(`/workspaces/${activeId}/facilities`, { token }),
    ]);
    setProducts(prods);
    setFacilities(facs);
  }, [token, activeId]);

  useEffect(() => {
    loadProducts().catch(() => setError("목록을 불러오지 못했습니다."));
  }, [loadProducts]);

  const loadIngredients = useCallback(
    async (productId: string) => {
      if (!token) return;
      const data = await api<Ingredient[]>(`/products/${productId}/ingredients`, { token });
      setIngredients(data);
    },
    [token]
  );

  async function selectProduct(p: Product) {
    setSelected(p);
    setMsg(null);
    await loadIngredients(p.id);
  }

  async function createProduct(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !activeId) return;
    await api(`/workspaces/${activeId}/products`, {
      method: "POST",
      token,
      body: { name: newProduct.name, category: newProduct.category || null },
    });
    setNewProduct({ name: "", category: "" });
    await loadProducts();
  }

  async function addIngredients() {
    if (!token || !selected) return;
    const names = rawNames.split(/[,;\n]/).map((s) => s.trim()).filter(Boolean);
    if (names.length === 0) return;
    await api(`/products/${selected.id}/ingredients/bulk`, {
      method: "POST",
      token,
      body: { raw_names: names },
    });
    setRawNames("");
    await loadIngredients(selected.id);
  }

  async function resolveFlag(ing: Ingredient) {
    if (!token) return;
    const inci = prompt("INCI 표준명을 입력하세요:", ing.inci_name ?? "");
    if (inci === null) return;
    await api(`/ingredients/${ing.id}`, {
      method: "PATCH",
      token,
      body: { inci_name: inci, flag: false },
    });
    if (selected) await loadIngredients(selected.id);
  }

  async function link() {
    if (!token || !selected || !linkFacility) return;
    await api(`/products/${selected.id}/facilities`, {
      method: "POST",
      token,
      body: { facility_id: linkFacility },
    });
    setMsg("✅ 시설 연동 완료");
  }

  async function generateListing() {
    if (!token || !selected) return;
    setMsg(null);
    try {
      await api(`/products/${selected.id}/generate-spl`, { method: "POST", token });
      setMsg("✅ 리스팅 SPL(5067) 생성 완료");
      await loadProducts();
    } catch (err) {
      const detail = err instanceof ApiError ? err.detail : null;
      const m =
        detail && typeof detail === "object" && "errors" in detail
          ? (detail as { errors: string[] }).errors.join(" / ")
          : "생성 실패";
      setMsg("⚠️ " + m);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">제품 리스팅 (Form 5067)</h1>
        <p className="mt-1 text-sm text-slate-500">
          제품·성분(INCI 자동 매핑)·시설 연동 후 리스팅 SPL을 생성합니다.
        </p>
      </div>

      <WorkspacePicker workspaces={workspaces} activeId={activeId} onSelect={selectWorkspace} />
      {error && <p className="text-sm text-red-600">{error}</p>}

      {activeId && (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Left: product list + create */}
          <div className="space-y-4">
            <form
              onSubmit={createProduct}
              className="flex flex-wrap gap-2 rounded-xl border border-slate-200 bg-white p-4"
            >
              <input
                placeholder="제품명 *"
                value={newProduct.name}
                onChange={(e) => setNewProduct({ ...newProduct, name: e.target.value })}
                className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
                required
              />
              <input
                placeholder="카테고리"
                value={newProduct.category}
                onChange={(e) => setNewProduct({ ...newProduct, category: e.target.value })}
                className="w-32 rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
              <button className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
                추가
              </button>
            </form>

            <div className="space-y-2">
              {products.length === 0 && (
                <p className="text-sm text-slate-400">등록된 제품이 없습니다.</p>
              )}
              {products.map((p) => (
                <button
                  key={p.id}
                  onClick={() => selectProduct(p)}
                  className={`flex w-full items-center justify-between rounded-lg border px-4 py-3 text-left ${
                    selected?.id === p.id
                      ? "border-brand-500 bg-brand-50"
                      : "border-slate-200 bg-white hover:bg-slate-50"
                  }`}
                >
                  <div>
                    <p className="text-sm font-medium text-slate-800">{p.name}</p>
                    <p className="text-xs text-slate-400">{p.category || "카테고리 없음"}</p>
                  </div>
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
                    {p.status}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Right: selected product detail */}
          <div>
            {selected ? (
              <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
                <h2 className="font-semibold text-slate-900">{selected.name}</h2>

                {/* Ingredients */}
                <div>
                  <p className="text-sm font-medium text-slate-700">성분 (INCI)</p>
                  <div className="mt-2 space-y-1">
                    {ingredients.length === 0 && (
                      <p className="text-xs text-slate-400">성분이 없습니다.</p>
                    )}
                    {ingredients.map((ing) => (
                      <div
                        key={ing.id}
                        className="flex items-center justify-between rounded-md bg-slate-50 px-3 py-1.5 text-sm"
                      >
                        <span className="text-slate-700">
                          {ing.raw_name}
                          <span className="text-slate-400"> → </span>
                          <span className="font-medium">{ing.inci_name ?? "미매핑"}</span>
                        </span>
                        <span className="flex items-center gap-2">
                          {ing.confidence && (
                            <span
                              className={`rounded-full px-2 py-0.5 text-xs ${
                                CONF_STYLE[ing.confidence] ?? "bg-slate-100"
                              }`}
                            >
                              {ing.confidence}
                            </span>
                          )}
                          {ing.flag && (
                            <button
                              onClick={() => resolveFlag(ing)}
                              className="rounded bg-amber-100 px-2 py-0.5 text-xs text-amber-700 hover:bg-amber-200"
                            >
                              검수
                            </button>
                          )}
                        </span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-2 flex gap-2">
                    <input
                      placeholder="성분 입력 (쉼표/줄바꿈 구분)"
                      value={rawNames}
                      onChange={(e) => setRawNames(e.target.value)}
                      className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    />
                    <button
                      onClick={addIngredients}
                      className="rounded-lg bg-slate-800 px-3 py-2 text-sm text-white hover:bg-slate-700"
                    >
                      매핑
                    </button>
                  </div>
                </div>

                {/* Facility link */}
                <div>
                  <p className="text-sm font-medium text-slate-700">시설 연동</p>
                  <div className="mt-2 flex gap-2">
                    <select
                      value={linkFacility}
                      onChange={(e) => setLinkFacility(e.target.value)}
                      className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    >
                      <option value="">시설 선택...</option>
                      {facilities.map((f) => (
                        <option key={f.id} value={f.id}>
                          {f.name_en} (FEI {f.fei || "—"})
                        </option>
                      ))}
                    </select>
                    <button
                      onClick={link}
                      disabled={!linkFacility}
                      className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-600 hover:bg-slate-100 disabled:opacity-50"
                    >
                      연동
                    </button>
                  </div>
                </div>

                <button
                  onClick={generateListing}
                  className="w-full rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-brand-700"
                >
                  리스팅 SPL 생성 (5067)
                </button>
                {msg && <p className="text-xs text-slate-600">{msg}</p>}
                <p className="text-xs text-slate-400">
                  * 성분 1개 이상 + 검수 플래그 해결 + 시설 연동이 완료돼야 생성됩니다.
                </p>
              </div>
            ) : (
              <div className="grid h-full place-items-center rounded-xl border border-dashed border-slate-300 p-10 text-center text-sm text-slate-400">
                왼쪽에서 제품을 선택하면
                <br />
                성분·시설·SPL 관리를 할 수 있습니다.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
