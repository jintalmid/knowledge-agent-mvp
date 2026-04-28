"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { getModelRoutes, getModelScenarios, getModels, ModelConfig, ModelRoute, ModelScenario, testModelRoute, updateModelRoute } from "@/lib/api";

const reservedScenarios = new Set(["document_parse_vision", "embedding_generation", "retrieval_rerank", "ppt_parse", "pdf_image_parse", "ocr"]);

function statusClass(status: string) {
  if (status === "ok") return "bg-emerald-50 text-emerald-700";
  if (status === "fallback" || status === "optional") return "bg-amber-50 text-amber-700";
  if (status === "disabled") return "bg-slate-100 text-slate-600";
  return "bg-red-50 text-red-700";
}

function RouteRow({
  route,
  models,
  description,
  isTesting,
  onSetModel,
  onTest,
}: {
  route: ModelRoute;
  models: ModelConfig[];
  description: string;
  isTesting: boolean;
  onSetModel: (route: ModelRoute, modelId: string) => void;
  onTest: (route: ModelRoute) => void;
}) {
  return (
    <article className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
      <div className="grid gap-4 lg:grid-cols-[1.2fr_22rem_auto]">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="break-all font-mono text-sm font-semibold text-slate-950">{route.scenario}</h2>
            <span className={`rounded-md px-2 py-1 text-xs font-medium ${statusClass(route.health_status)}`}>{route.health_status}</span>
            {route.is_required ? <span className="rounded-md bg-red-50 px-2 py-1 text-xs font-medium text-red-700">required</span> : null}
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-600">{description || route.health_message}</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {route.required_tags_json.map((tag) => (
              <span className="rounded-md bg-slate-100 px-2 py-1 font-mono text-xs text-slate-600" key={tag}>{tag}</span>
            ))}
          </div>
        </div>

        <div>
          <label className="text-xs font-medium text-slate-500">场景模型</label>
          <select
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={route.model_id || ""}
            onChange={(event) => onSetModel(route, event.target.value)}
          >
            <option value="">未配置，使用 fallback</option>
            {models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.display_name} / {model.model_name}
              </option>
            ))}
          </select>
          <p className="mt-2 break-all text-xs text-slate-500">
            当前：{route.model_display_name || "未配置"} {route.provider_name ? `/ ${route.provider_name}` : ""}
          </p>
          <p className="mt-1 text-xs text-slate-500">fallback: {route.fallback_scenario || "无"} / {route.health_message}</p>
        </div>

        <div className="flex items-start justify-end">
          <button
            className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:text-slate-400"
            disabled={isTesting}
            onClick={() => onTest(route)}
            type="button"
          >
            {isTesting ? "测试中" : "测试"}
          </button>
        </div>
      </div>
    </article>
  );
}

export default function ModelRoutingClient() {
  const [routes, setRoutes] = useState<ModelRoute[]>([]);
  const [models, setModels] = useState<ModelConfig[]>([]);
  const [scenarios, setScenarios] = useState<ModelScenario[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [testingScenario, setTestingScenario] = useState<string | null>(null);

  const scenarioDescriptions = useMemo(
    () => Object.fromEntries(scenarios.map((scenario) => [scenario.scenario, scenario.description])),
    [scenarios],
  );
  const activeRoutes = routes.filter((route) => !reservedScenarios.has(route.scenario));
  const reservedRoutes = routes.filter((route) => reservedScenarios.has(route.scenario));
  const healthyCount = routes.filter((route) => route.health_status === "ok" || route.health_status === "fallback" || route.health_status === "optional").length;
  const defaultRoute = routes.find((route) => route.scenario === "default_text");

  async function refresh() {
    setError(null);
    try {
      const [loadedRoutes, loadedModels, loadedScenarios] = await Promise.all([getModelRoutes(), getModels(), getModelScenarios()]);
      setRoutes(loadedRoutes);
      setModels(loadedModels);
      setScenarios(loadedScenarios);
    } catch (err) {
      setError(err instanceof Error ? err.message : "模型路由加载失败");
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function onSetModel(route: ModelRoute, modelId: string) {
    setError(null);
    setMessage(null);
    try {
      await updateModelRoute(route.scenario, { model_id: modelId || null });
      setMessage(`${route.scenario} 已更新`);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "路由更新失败");
    }
  }

  async function onTest(route: ModelRoute) {
    setTestingScenario(route.scenario);
    setError(null);
    setMessage(null);
    try {
      const result = await testModelRoute(route.scenario);
      setMessage(`${route.scenario} 测试成功：${result.response_preview || result.message}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "路由测试失败");
    } finally {
      setTestingScenario(null);
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-7xl px-6 py-10">
      <header className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">M04 Model Routing</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">模型路由</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
            为每个 LLM scenario 选择专用模型；未配置时回退到 fallback 或 default_text。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link className="rounded-md bg-slate-950 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800" href="/settings/models">
            模型管理
          </Link>
          <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-white" href="/debug/llm-logs">
            调用日志
          </Link>
        </div>
      </header>

      {error ? <div className="mb-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
      {message ? <div className="mb-5 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{message}</div> : null}

      <section className="mb-6 grid gap-4 md:grid-cols-3">
        <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">路由健康</p>
          <p className="mt-2 text-lg font-semibold text-slate-950">{healthyCount} / {routes.length}</p>
          <p className="mt-1 text-xs text-slate-500">ok、fallback、optional 视为可用</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">default_text</p>
          <p className="mt-2 truncate text-lg font-semibold text-slate-950">{defaultRoute?.model_display_name || "未配置"}</p>
          <p className="mt-1 truncate text-xs text-slate-500">{defaultRoute?.health_message || "default_text 是必需项"}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">可选预留能力</p>
          <p className="mt-2 text-lg font-semibold text-slate-950">{reservedRoutes.length}</p>
          <p className="mt-1 text-xs text-slate-500">多模态、embedding、OCR 等暂不启用</p>
        </div>
      </section>

      <section className="grid gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-slate-950">当前业务场景</h2>
          <span className="text-sm text-slate-500">{activeRoutes.length} 个 scenario</span>
        </div>
        {activeRoutes.map((route) => (
          <RouteRow
            description={scenarioDescriptions[route.scenario] || ""}
            isTesting={testingScenario === route.scenario}
            key={route.scenario}
            models={models}
            onSetModel={onSetModel}
            onTest={onTest}
            route={route}
          />
        ))}
      </section>

      <section className="mt-8">
        <details className="rounded-md border border-slate-200 bg-white shadow-sm">
          <summary className="cursor-pointer px-5 py-4 text-sm font-semibold text-slate-950">预留能力场景</summary>
          <div className="grid gap-3 border-t border-slate-100 p-4">
            {reservedRoutes.map((route) => (
              <RouteRow
                description={scenarioDescriptions[route.scenario] || ""}
                isTesting={testingScenario === route.scenario}
                key={route.scenario}
                models={models}
                onSetModel={onSetModel}
                onTest={onTest}
                route={route}
              />
            ))}
          </div>
        </details>
      </section>
    </main>
  );
}
