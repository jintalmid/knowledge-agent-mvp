"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { startAgentRun } from "@/lib/api";

export default function AgentClient({ taskId }: { taskId: string }) {
  const router = useRouter();
  const [question, setQuestion] = useState("");
  const [maxIterations, setMaxIterations] = useState(10);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onStart(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!question.trim()) {
      setError("请输入问题");
      return;
    }

    setIsRunning(true);
    setError(null);
    try {
      const response = await startAgentRun(taskId, {
        question: question.trim(),
        max_iterations: maxIterations,
      });
      router.push(`/tasks/${taskId}/runs/${response.agent_run_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Agent Run 启动失败");
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-6 py-10">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link className="text-sm font-medium text-slate-600 hover:underline" href={`/tasks/${taskId}`}>
            返回任务详情
          </Link>
          <p className="mt-4 text-sm font-medium text-slate-500">v0.3 Agent Runner</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">启动 Agent Run</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
            Agent 会按 plan、tool call、observation、reflection、decision 的循环运行，并在停止后生成最终答案。
          </p>
        </div>
        <Link
          className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-white"
          href={`/tasks/${taskId}/results`}
        >
          历史结果
        </Link>
      </header>

      {error ? <div className="mb-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

      <form className="grid gap-5 rounded-md border border-slate-200 bg-white p-5 shadow-sm" onSubmit={onStart}>
        <label className="grid gap-1.5">
          <span className="text-sm font-medium text-slate-700">问题</span>
          <textarea
            className="min-h-36 rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
            maxLength={4000}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="输入希望 Agent 通过文件摘要、文本读取或 Excel 分析来回答的问题"
            value={question}
          />
        </label>

        <label className="grid max-w-xs gap-1.5">
          <span className="text-sm font-medium text-slate-700">max_iterations</span>
          <input
            className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
            max={10}
            min={1}
            onChange={(event) => setMaxIterations(Number(event.target.value))}
            type="number"
            value={maxIterations}
          />
        </label>

        <button
          className="w-fit rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          disabled={isRunning}
          type="submit"
        >
          {isRunning ? "运行中" : "启动 Agent Run"}
        </button>
      </form>
    </main>
  );
}
