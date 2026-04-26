"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getLlmSettings, LlmSettings, LlmTestResult, testLlm } from "@/lib/api";

export default function LlmSettingsClient() {
  const [settings, setSettings] = useState<LlmSettings | null>(null);
  const [testResult, setTestResult] = useState<LlmTestResult | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setError(null);
    try {
      setSettings(await getLlmSettings());
    } catch (err) {
      setError(err instanceof Error ? err.message : "LLM 设置加载失败");
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function onTest() {
    setIsTesting(true);
    setError(null);
    setTestResult(null);
    try {
      setTestResult(await testLlm());
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "LLM 测试失败");
    } finally {
      setIsTesting(false);
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-6 py-10">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">LLM Settings</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">LLM 设置</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
            当前只支持 openai_compatible，通过 backend/.env 配置。
          </p>
        </div>
        <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-white" href="/debug/llm-logs">
          调用日志
        </Link>
      </header>

      {error ? <div className="mb-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

      <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
        <dl className="grid gap-4 md:grid-cols-2">
          <div>
            <dt className="text-xs font-medium text-slate-500">provider_type</dt>
            <dd className="mt-1 font-mono text-sm text-slate-900">{settings?.provider_type ?? "未配置"}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-slate-500">model</dt>
            <dd className="mt-1 font-mono text-sm text-slate-900">{settings?.model ?? "未配置"}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-slate-500">base_url</dt>
            <dd className="mt-1 font-mono text-sm text-slate-900">{settings?.base_url_configured ? "已配置" : "未配置"}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-slate-500">api_key</dt>
            <dd className="mt-1 font-mono text-sm text-slate-900">{settings?.api_key_configured ? "已配置" : "未配置"}</dd>
          </div>
        </dl>
        <div className="mt-5 flex items-center gap-3">
          <button
            className="rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={isTesting}
            onClick={onTest}
            type="button"
          >
            {isTesting ? "测试中" : "测试 LLM"}
          </button>
          <span className={settings?.ready ? "text-sm text-emerald-700" : "text-sm text-red-700"}>
            {settings?.ready ? "配置完整" : "配置不完整"}
          </span>
        </div>
      </section>

      {testResult ? (
        <section className="mt-5 rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
          <p className="font-medium">{testResult.status}</p>
          <p className="mt-2">{testResult.response_preview}</p>
          <p className="mt-2 font-mono text-xs">{testResult.log_id}</p>
        </section>
      ) : null}
    </main>
  );
}
