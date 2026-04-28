"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getApiBaseUrl, getLlmSettings, LlmSettings, LlmTestResult, testLlm } from "@/lib/api";

export default function LlmSettingsClient() {
  const [settings, setSettings] = useState<LlmSettings | null>(null);
  const [testResult, setTestResult] = useState<LlmTestResult | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setIsLoading(true);
    setError(null);
    try {
      setSettings(await getLlmSettings());
    } catch (err) {
      setSettings(null);
      setError(err instanceof Error ? err.message : "LLM 设置加载失败");
    } finally {
      setIsLoading(false);
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
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">LLM Settings</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">兼容 LLM 配置</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
            当前页面显示 legacy `.env` 配置状态；业务调用已通过模型管理和 scenario 路由选择模型。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-white" href="/settings/models">
            模型管理
          </Link>
          <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-white" href="/debug/llm-logs">
            调用日志
          </Link>
        </div>
      </header>

      {error ? <div className="mb-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

      <section className="mb-6 grid gap-4 md:grid-cols-3">
        <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">配置状态</p>
          <p className={settings?.ready ? "mt-2 text-lg font-semibold text-emerald-700" : "mt-2 text-lg font-semibold text-red-700"}>
            {isLoading ? "读取中" : settings?.ready ? "可种子化" : "不完整"}
          </p>
          <p className="mt-1 text-xs text-slate-500">业务调用以模型管理为准</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">Provider</p>
          <p className="mt-2 truncate font-mono text-sm font-semibold text-slate-950">{isLoading ? "读取中" : settings?.provider_type || "未配置"}</p>
          <p className="mt-1 truncate text-xs text-slate-500">{settings?.base_url || "无 base_url"}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">Legacy Model</p>
          <p className="mt-2 truncate font-mono text-sm font-semibold text-slate-950">{isLoading ? "读取中" : settings?.model || "未配置"}</p>
          <p className="mt-1 text-xs text-slate-500">timeout: {settings ? `${settings.timeout_seconds}s` : "未知"}</p>
        </div>
      </section>

      <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-5 flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-950">后端读取到的 LLM 配置</h2>
            <p className="mt-1 text-sm leading-6 text-slate-500">
              数据库初始化会将这组配置种子化为 default_text 模型；新模型请到“模型管理”维护。
            </p>
          </div>
          <span
            className={
              isLoading
                ? "rounded-md bg-slate-100 px-2.5 py-1 text-sm font-medium text-slate-600"
                : settings?.ready
                  ? "rounded-md bg-emerald-50 px-2.5 py-1 text-sm font-medium text-emerald-700"
                  : "rounded-md bg-red-50 px-2.5 py-1 text-sm font-medium text-red-700"
            }
          >
            {isLoading ? "读取中" : settings?.ready ? "配置项完整" : "配置项不完整"}
          </span>
        </div>

        <details className="rounded-md border border-slate-100 bg-slate-50">
          <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-slate-800">查看 legacy .env 详情</summary>
          <dl className="grid gap-4 border-t border-slate-100 p-4 md:grid-cols-2">
            <div>
              <dt className="text-xs font-medium text-slate-500">配置来源</dt>
              <dd className="mt-1 text-sm text-slate-900">{isLoading ? "加载中" : settings?.config_source ?? "未从后端返回"}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-slate-500">配置文件</dt>
              <dd className="mt-1 break-all font-mono text-sm text-slate-900">
                {isLoading ? "加载中" : settings?.env_file_path ?? "未从后端返回"}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-slate-500">前端连接的后端 API</dt>
              <dd className="mt-1 break-all font-mono text-sm text-slate-900">{getApiBaseUrl()}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium text-slate-500">LLM api_key</dt>
              <dd className="mt-1 font-mono text-sm text-slate-900">
                {isLoading ? "加载中" : settings?.api_key_configured ? "已配置，已隐藏" : "未配置"}
              </dd>
            </div>
          </dl>
        </details>
        <div className="mt-5 flex items-center gap-3">
          <button
            className="rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={isTesting}
            onClick={onTest}
            type="button"
          >
            {isTesting ? "测试中" : "测试 LLM"}
          </button>
          <button
            className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            onClick={refresh}
            type="button"
          >
            刷新状态
          </button>
        </div>
        <p className="mt-3 text-xs leading-5 text-slate-500">
          配置项完整只表示后端已读取到 provider、base_url、api_key 和 model。真实可用性以“测试 LLM”的结果为准；环境变量会覆盖同名 .env 配置。
        </p>
      </section>

      {testResult ? (
        <section className="mt-5 rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
          <p className="font-medium">连接测试成功</p>
          <p className="mt-2">{testResult.response_preview}</p>
          <p className="mt-2 font-mono text-xs">{testResult.log_id}</p>
        </section>
      ) : null}
    </main>
  );
}
