"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import Pagination from "@/components/Pagination";
import { getLlmLogs, LlmCallLog } from "@/lib/api";
import { usePagination } from "@/lib/usePagination";

type ExpandedPanel = "request" | "response";

function formatContent(value: string | null | undefined) {
  if (!value) {
    return "无内容";
  }

  const trimmed = value.trim();
  if (!trimmed) {
    return "无内容";
  }

  try {
    return JSON.stringify(JSON.parse(trimmed), null, 2);
  } catch {
    return trimmed;
  }
}

export default function LlmLogsClient() {
  const [logs, setLogs] = useState<LlmCallLog[]>([]);
  const [expandedPanels, setExpandedPanels] = useState<Record<string, ExpandedPanel | null>>({});
  const [error, setError] = useState<string | null>(null);
  const logPagination = usePagination(logs, 10);

  async function refresh() {
    setError(null);
    try {
      setLogs(await getLlmLogs());
    } catch (err) {
      setError(err instanceof Error ? err.message : "日志加载失败");
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  function togglePanel(logId: string, panel: ExpandedPanel) {
    setExpandedPanels((current) => ({
      ...current,
      [logId]: current[logId] === panel ? null : panel,
    }));
  }

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">M13 Debug</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">LLM 调用日志</h1>
        </div>
        <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-white" href="/settings/llm">
          LLM 设置
        </Link>
      </header>

      {error ? <div className="mb-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

      <section className="grid gap-3">
        {logPagination.paginatedItems.map((log) => {
          const expandedPanel = expandedPanels[log.id] ?? null;
          const responseContent = log.error_message || log.response_preview || "无响应";

          return (
            <article key={log.id} className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="font-mono text-xs text-slate-500">{log.id}</span>
                    <span
                      className={
                        log.status === "success"
                          ? "rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700"
                          : "rounded-md bg-red-50 px-2 py-1 text-xs font-medium text-red-700"
                      }
                    >
                      {log.status}
                    </span>
                  </div>
                  <p className="mt-2 text-sm font-semibold text-slate-950">{log.module_name}</p>
                  <div className="mt-3 grid gap-2 text-sm text-slate-600 md:grid-cols-2">
                    <p>
                      <span className="text-slate-400">任务：</span>
                      {log.task_id ? (
                        <Link className="font-medium text-slate-800 hover:underline" href={`/tasks/${log.task_id}`}>
                          {log.task_name || log.task_id}
                        </Link>
                      ) : (
                        <span className="text-slate-500">无任务上下文</span>
                      )}
                    </p>
                    <p>
                      <span className="text-slate-400">用户 / 团队：</span>
                      {log.owner_user_id || "无"} / {log.department_id || "无"}
                    </p>
                    <p>
                      <span className="text-slate-400">Agent Run：</span>
                      <span className="font-mono text-xs">{log.agent_run_id || "无"}</span>
                    </p>
                    <p>
                      <span className="text-slate-400">Iteration：</span>
                      <span className="font-mono text-xs">{log.iteration_id || "无"}</span>
                    </p>
                  </div>
                  <p className="mt-3 font-mono text-xs text-slate-500">
                    {log.provider_type} / {log.model_name} / {log.latency_ms}ms
                    {log.security_level ? ` / ${log.security_level}` : ""}
                  </p>
                </div>
                <div className="flex flex-col items-start gap-3 sm:items-end">
                  <p className="text-xs text-slate-500">{new Date(log.created_at).toLocaleString("zh-CN")}</p>
                  <div className="flex flex-wrap gap-2">
                    <button
                      className={
                        expandedPanel === "request"
                          ? "rounded-md bg-slate-950 px-3 py-2 text-sm font-medium text-white"
                          : "rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                      }
                      onClick={() => togglePanel(log.id, "request")}
                      type="button"
                    >
                      请求内容
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
                      响应内容
                    </button>
                  </div>
                </div>
              </div>

              {expandedPanel ? (
                <div className="mt-4 rounded-md border border-slate-200 bg-slate-50">
                  <div className="border-b border-slate-200 px-4 py-2 text-sm font-medium text-slate-700">
                    {expandedPanel === "request" ? "请求内容" : "响应内容"}
                  </div>
                  <pre className="max-h-[32rem] overflow-auto whitespace-pre-wrap break-words p-4 text-sm leading-6 text-slate-800">
                    {expandedPanel === "request" ? formatContent(log.prompt_preview) : formatContent(responseContent)}
                  </pre>
                </div>
              ) : null}
            </article>
          );
        })}
        {logs.length === 0 ? <p className="text-sm text-slate-500">暂无 LLM 调用日志</p> : null}
        {logs.length > 0 ? (
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
