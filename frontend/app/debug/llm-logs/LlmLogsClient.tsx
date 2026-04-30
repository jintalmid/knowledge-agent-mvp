"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import Pagination from "@/components/Pagination";
import { getLlmLogs, getModelProviders, getModels, getModelScenarios, LlmCallLog, ModelConfig, ModelProvider, ModelScenario } from "@/lib/api";
import { usePagination } from "@/lib/usePagination";

type ExpandedPanel = "request" | "response";

function formatContent(value: string | null | undefined) {
  if (!value?.trim()) {
    return "无内容";
  }

  try {
    return JSON.stringify(JSON.parse(value.trim()), null, 2);
  } catch {
    return value.trim();
  }
}

function shortId(value: string | null | undefined) {
  if (!value) {
    return "无";
  }
  if (value.length <= 18) {
    return value;
  }
  return `${value.slice(0, 10)}...${value.slice(-6)}`;
}

function formatTime(value: string) {
  return new Date(value).toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function statusClass(status: string) {
  if (status === "success") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700";
  }
  return "border-red-200 bg-red-50 text-red-700";
}

function latencyClass(latency: number) {
  if (latency >= 30000) return "text-red-700";
  if (latency >= 10000) return "text-amber-700";
  return "text-slate-950";
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="min-w-0">
      <p className="text-xs font-medium text-slate-400">{label}</p>
      <div className="mt-1 min-w-0 text-sm text-slate-700">{children}</div>
    </div>
  );
}

export default function LlmLogsClient() {
  const [logs, setLogs] = useState<LlmCallLog[]>([]);
  const [scenarios, setScenarios] = useState<ModelScenario[]>([]);
  const [models, setModels] = useState<ModelConfig[]>([]);
  const [providers, setProviders] = useState<ModelProvider[]>([]);
  const [filters, setFilters] = useState({ scenario: "", model_id: "", provider_id: "", status: "" });
  const [expandedPanels, setExpandedPanels] = useState<Record<string, ExpandedPanel | null>>({});
  const [error, setError] = useState<string | null>(null);

  const visibleLogs = useMemo(() => {
    return filters.status ? logs.filter((log) => log.status === filters.status) : logs;
  }, [filters.status, logs]);

  const logPagination = usePagination(visibleLogs, 10);

  const modelNameById = useMemo(() => {
    return Object.fromEntries(models.map((model) => [model.id, model.display_name]));
  }, [models]);

  const providerNameById = useMemo(() => {
    return Object.fromEntries(providers.map((provider) => [provider.id, provider.name]));
  }, [providers]);

  const stats = useMemo(() => {
    const successCount = visibleLogs.filter((log) => log.status === "success").length;
    const failedCount = visibleLogs.filter((log) => log.status !== "success").length;
    const avgLatency = visibleLogs.length > 0
      ? Math.round(visibleLogs.reduce((total, log) => total + log.latency_ms, 0) / visibleLogs.length)
      : 0;
    const scenarioCount = new Set(visibleLogs.map((log) => log.scenario || "unknown")).size;
    return { avgLatency, failedCount, scenarioCount, successCount };
  }, [visibleLogs]);

  async function refresh() {
    setError(null);
    try {
      const [loadedLogs, loadedScenarios, loadedModels, loadedProviders] = await Promise.all([
        getLlmLogs({
          scenario: filters.scenario || undefined,
          model_id: filters.model_id || undefined,
          provider_id: filters.provider_id || undefined,
        }),
        getModelScenarios(),
        getModels(),
        getModelProviders(),
      ]);
      setLogs(loadedLogs);
      setScenarios(loadedScenarios);
      setModels(loadedModels);
      setProviders(loadedProviders);
    } catch (err) {
      setError(err instanceof Error ? err.message : "日志加载失败");
    }
  }

  useEffect(() => {
    refresh();
  }, [filters.scenario, filters.model_id, filters.provider_id]);

  function togglePanel(logId: string, panel: ExpandedPanel) {
    setExpandedPanels((current) => ({
      ...current,
      [logId]: current[logId] === panel ? null : panel,
    }));
  }

  function clearFilters() {
    setFilters({ scenario: "", model_id: "", provider_id: "", status: "" });
  }

  return (
    <main className="mx-auto min-h-screen max-w-7xl px-6 py-10">
      <header className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">M13 Debug Console</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">LLM 调用日志</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
            按 scenario、模型和 Provider 追踪每次 LLM 调用。Request / Response 默认隐藏，需要时再展开查看。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link className="rounded-md bg-slate-950 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800" href="/settings/models">
            模型管理
          </Link>
          <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-white" href="/settings/model-routing">
            模型路由
          </Link>
        </div>
      </header>

      {error ? <div className="mb-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

      <section className="mb-5 grid gap-4 md:grid-cols-4">
        <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">当前日志</p>
          <p className="mt-2 text-2xl font-semibold text-slate-950">{visibleLogs.length}</p>
          <p className="mt-1 text-xs text-slate-500">筛选后的调用数</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">成功 / 失败</p>
          <p className="mt-2 text-2xl font-semibold text-slate-950">{stats.successCount} / {stats.failedCount}</p>
          <p className="mt-1 text-xs text-slate-500">失败日志会以红色标记</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">平均耗时</p>
          <p className={`mt-2 text-2xl font-semibold ${latencyClass(stats.avgLatency)}`}>{stats.avgLatency}ms</p>
          <p className="mt-1 text-xs text-slate-500">仅统计当前筛选结果</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">涉及场景</p>
          <p className="mt-2 text-2xl font-semibold text-slate-950">{stats.scenarioCount}</p>
          <p className="mt-1 text-xs text-slate-500">scenario 路由覆盖面</p>
        </div>
      </section>

      <section className="mb-6 rounded-md border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-4 py-3">
          <div>
            <h2 className="text-sm font-semibold text-slate-950">筛选</h2>
            <p className="mt-1 text-xs text-slate-500">用于定位某个业务场景、模型或 Provider 的调用问题。</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50" onClick={refresh} type="button">
              刷新
            </button>
            <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50" onClick={clearFilters} type="button">
              清空筛选
            </button>
          </div>
        </div>
        <div className="grid gap-4 p-4 lg:grid-cols-2 2xl:grid-cols-[minmax(14rem,1fr)_minmax(16rem,1.2fr)_minmax(16rem,1.2fr)_minmax(10rem,0.8fr)]">
          <label className="grid min-w-0 gap-1 text-sm">
            <span className="text-xs font-medium text-slate-500">Scenario</span>
            <select className="w-full rounded-md border border-slate-300 bg-white px-3 py-2" value={filters.scenario} onChange={(event) => setFilters({ ...filters, scenario: event.target.value })}>
              <option value="">全部场景</option>
              {scenarios.map((scenario) => <option key={scenario.scenario} value={scenario.scenario}>{scenario.scenario}</option>)}
            </select>
          </label>
          <label className="grid min-w-0 gap-1 text-sm">
            <span className="text-xs font-medium text-slate-500">Model</span>
            <select className="w-full rounded-md border border-slate-300 bg-white px-3 py-2" value={filters.model_id} onChange={(event) => setFilters({ ...filters, model_id: event.target.value })}>
              <option value="">全部模型</option>
              {models.map((model) => <option key={model.id} value={model.id}>{model.display_name}</option>)}
            </select>
          </label>
          <label className="grid min-w-0 gap-1 text-sm">
            <span className="text-xs font-medium text-slate-500">Provider</span>
            <select className="w-full rounded-md border border-slate-300 bg-white px-3 py-2" value={filters.provider_id} onChange={(event) => setFilters({ ...filters, provider_id: event.target.value })}>
              <option value="">全部 Provider</option>
              {providers.map((provider) => <option key={provider.id} value={provider.id}>{provider.name}</option>)}
            </select>
          </label>
          <label className="grid min-w-0 gap-1 text-sm">
            <span className="text-xs font-medium text-slate-500">Status</span>
            <select className="w-full rounded-md border border-slate-300 bg-white px-3 py-2" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
              <option value="">全部状态</option>
              <option value="success">success</option>
              <option value="failed">failed</option>
            </select>
          </label>
        </div>
      </section>

      <section className="grid gap-3">
        {logPagination.paginatedItems.map((log) => {
          const expandedPanel = expandedPanels[log.id] ?? null;
          const responseContent = log.error_message || log.response_preview || "无响应";
          const modelLabel = log.model_id ? modelNameById[log.model_id] || log.model_name : log.model_name;
          const providerLabel = log.provider_id ? providerNameById[log.provider_id] || log.provider_type : log.provider_type;

          return (
            <article key={log.id} className={`overflow-hidden rounded-md border bg-white shadow-sm ${log.status === "success" ? "border-slate-200" : "border-red-200"}`}>
              <div className={log.status === "success" ? "h-1 bg-slate-200" : "h-1 bg-red-500"} />
              <div className="grid gap-4 px-4 py-4 xl:grid-cols-[1.15fr_1fr_auto]">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`rounded-md border px-2 py-1 text-xs font-semibold ${statusClass(log.status)}`}>{log.status}</span>
                    <span className="rounded-md bg-slate-100 px-2 py-1 font-mono text-xs text-slate-700">{log.scenario || "no_scenario"}</span>
                    <span className="text-xs text-slate-400">{formatTime(log.created_at)}</span>
                  </div>
                  <h2 className="mt-3 text-base font-semibold text-slate-950">{log.module_name}</h2>
                  <p className="mt-2 min-w-0 break-all font-mono text-xs text-slate-500">log: {shortId(log.id)}</p>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <Field label="任务">
                    {log.task_id ? (
                      <Link className="font-medium text-slate-900 hover:underline" href={`/tasks/${log.task_id}`}>
                        {log.task_name || shortId(log.task_id)}
                      </Link>
                    ) : (
                      <span className="text-slate-500">无任务上下文</span>
                    )}
                  </Field>
                  <Field label="用户 / 团队">
                    <span>{log.owner_user_id || "无"} / {log.department_id || "无"}</span>
                  </Field>
                  <Field label="Provider">
                    <span className="break-all">{providerLabel}</span>
                  </Field>
                  <Field label="Model">
                    <span className="break-all">{modelLabel}</span>
                  </Field>
                </div>

                <div className="flex flex-col gap-3 xl:min-w-52 xl:items-end">
                  <div className="text-left xl:text-right">
                    <p className="text-xs font-medium text-slate-400">Latency</p>
                    <p className={`mt-1 text-xl font-semibold ${latencyClass(log.latency_ms)}`}>{log.latency_ms}ms</p>
                  </div>
                  <div className="flex flex-wrap gap-2 xl:justify-end">
                    <button
                      className={
                        expandedPanel === "request"
                          ? "rounded-md bg-slate-950 px-3 py-2 text-sm font-medium text-white"
                          : "rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                      }
                      onClick={() => togglePanel(log.id, "request")}
                      type="button"
                    >
                      Request
                    </button>
                    <button
                      className={
                        expandedPanel === "response"
                          ? "rounded-md bg-slate-950 px-3 py-2 text-sm font-medium text-white"
                          : "rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                      }
                      onClick={() => togglePanel(log.id, "response")}
                      type="button"
                    >
                      Response
                    </button>
                  </div>
                </div>
              </div>

              <details className="border-t border-slate-100 px-4 py-3">
                <summary className="cursor-pointer text-sm font-medium text-slate-600">技术详情</summary>
                <dl className="mt-3 grid gap-3 text-sm md:grid-cols-3">
                  <div>
                    <dt className="text-xs font-medium text-slate-400">Agent Run</dt>
                    <dd className="mt-1 break-all font-mono text-xs text-slate-700">{log.agent_run_id || "无"}</dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium text-slate-400">Iteration</dt>
                    <dd className="mt-1 break-all font-mono text-xs text-slate-700">{log.iteration_id || "无"}</dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium text-slate-400">Security</dt>
                    <dd className="mt-1 text-slate-700">{log.security_level || "无"}</dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium text-slate-400">Provider ID</dt>
                    <dd className="mt-1 break-all font-mono text-xs text-slate-700">{log.provider_id || "无"}</dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium text-slate-400">Model ID</dt>
                    <dd className="mt-1 break-all font-mono text-xs text-slate-700">{log.model_id || "无"}</dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium text-slate-400">Provider Type / Model Name</dt>
                    <dd className="mt-1 break-all font-mono text-xs text-slate-700">{log.provider_type} / {log.model_name}</dd>
                  </div>
                </dl>
              </details>

              {expandedPanel ? (
                <div className="border-t border-slate-100 bg-slate-950">
                  <div className="flex items-center justify-between gap-3 border-b border-slate-800 px-4 py-2">
                    <p className="text-sm font-semibold text-slate-100">
                      {expandedPanel === "request" ? "Request Payload" : log.status === "success" ? "Response Payload" : "Error / Response"}
                    </p>
                    <button className="text-xs font-medium text-slate-400 hover:text-white" onClick={() => togglePanel(log.id, expandedPanel)} type="button">
                      收起
                    </button>
                  </div>
                  <pre className="max-h-[34rem] overflow-auto whitespace-pre-wrap break-words p-4 text-sm leading-6 text-slate-100">
                    {expandedPanel === "request" ? formatContent(log.prompt_preview) : formatContent(responseContent)}
                  </pre>
                </div>
              ) : null}
            </article>
          );
        })}

        {visibleLogs.length === 0 ? (
          <div className="rounded-md border border-dashed border-slate-300 bg-white px-5 py-10 text-center">
            <p className="text-sm font-medium text-slate-700">暂无匹配的 LLM 调用日志</p>
            <p className="mt-2 text-sm text-slate-500">可以清空筛选，或先在模型、摘要、Agent Run 页面触发一次 LLM 调用。</p>
          </div>
        ) : null}

        {visibleLogs.length > 0 ? (
          <Pagination
            label="条日志"
            onPageChange={logPagination.setPage}
            onPageSizeChange={logPagination.setPageSize}
            page={logPagination.page}
            pageSize={logPagination.pageSize}
            totalItems={logPagination.totalItems}
            totalPages={logPagination.totalPages}
          />
        ) : null}
      </section>
    </main>
  );
}
