"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getLlmLogs, LlmCallLog } from "@/lib/api";

export default function LlmLogsClient() {
  const [logs, setLogs] = useState<LlmCallLog[]>([]);
  const [error, setError] = useState<string | null>(null);

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
        {logs.map((log) => (
          <article key={log.id} className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="flex flex-wrap items-center gap-3">
                  <span className="font-mono text-xs text-slate-500">{log.id}</span>
                  <span className={log.status === "success" ? "rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700" : "rounded-md bg-red-50 px-2 py-1 text-xs font-medium text-red-700"}>
                    {log.status}
                  </span>
                </div>
                <p className="mt-2 text-sm font-medium text-slate-950">{log.module_name}</p>
                <p className="mt-1 font-mono text-xs text-slate-500">
                  {log.provider_type} / {log.model_name} / {log.latency_ms}ms
                </p>
              </div>
              <p className="text-xs text-slate-500">{new Date(log.created_at).toLocaleString("zh-CN")}</p>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <pre className="max-h-64 overflow-auto rounded-md bg-slate-950 p-3 text-xs leading-6 text-slate-100">{log.prompt_preview}</pre>
              <pre className="max-h-64 overflow-auto rounded-md bg-slate-950 p-3 text-xs leading-6 text-slate-100">
                {log.error_message || log.response_preview || "无响应"}
              </pre>
            </div>
          </article>
        ))}
        {logs.length === 0 ? <p className="text-sm text-slate-500">暂无 LLM 调用日志</p> : null}
      </section>
    </main>
  );
}
