"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { Answer, askTaskQuestion } from "@/lib/api";
import { copyText } from "@/lib/clipboard";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function AskClient({ taskId }: { taskId: string }) {
  const [questionText, setQuestionText] = useState("");
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [isAsking, setIsAsking] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onAsk(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!questionText.trim()) {
      setError("请输入问题");
      return;
    }

    setIsAsking(true);
    setCopied(false);
    setError(null);
    try {
      const result = await askTaskQuestion(taskId, questionText.trim());
      setAnswer(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "问答失败");
    } finally {
      setIsAsking(false);
    }
  }

  async function onCopy() {
    if (!answer) {
      return;
    }
    try {
      await copyText(answer.answer_text_markdown);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch (err) {
      setError(err instanceof Error ? err.message : "复制失败");
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link className="text-sm font-medium text-slate-600 hover:underline" href={`/tasks/${taskId}`}>
            返回任务详情
          </Link>
          <p className="mt-4 text-sm font-medium text-slate-500">M09 Text QA</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">文本问答</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
            基于临时检索选出的文本文件生成 Markdown 答案。
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-white" href={`/tasks/${taskId}/retrieval`}>
            检索设置
          </Link>
          <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-white" href={`/tasks/${taskId}/results`}>
            历史结果
          </Link>
        </div>
      </header>

      {error ? <div className="mb-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

      <form className="mb-6 rounded-md border border-slate-200 bg-white p-5 shadow-sm" onSubmit={onAsk}>
        <label className="grid gap-1.5">
          <span className="text-sm font-medium text-slate-700">问题</span>
          <textarea
            className="min-h-32 rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
            maxLength={4000}
            onChange={(event) => setQuestionText(event.target.value)}
            placeholder="输入一个需要从已解析文本文件中回答的问题"
            value={questionText}
          />
        </label>
        <button
          className="mt-4 rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          disabled={isAsking}
          type="submit"
        >
          {isAsking ? "生成中" : "生成答案"}
        </button>
      </form>

      {answer ? (
        <section className="grid gap-4">
          <article className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-slate-500">{formatDate(answer.created_at)}</p>
                <h2 className="mt-1 text-lg font-semibold text-slate-950">{answer.question_text}</h2>
              </div>
              <button
                className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                onClick={onCopy}
                type="button"
              >
                {copied ? "已复制" : "复制 Markdown"}
              </button>
            </div>
            <div className="whitespace-pre-wrap rounded-md bg-slate-50 p-4 text-sm leading-7 text-slate-800">
              {answer.answer_text_markdown}
            </div>
            <p className="mt-3 font-mono text-xs text-slate-500">
              {answer.llm_provider} / {answer.llm_model}
            </p>
          </article>

          <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-950">来源文件</h2>
            <div className="mt-4 grid gap-3">
              {answer.source_refs_json.map((source) => (
                <div key={source.task_file_id} className="rounded-md border border-slate-100 p-3">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-medium text-slate-900">{source.display_name}</p>
                      <p className="mt-1 break-all font-mono text-xs text-slate-500">{source.task_file_id}</p>
                    </div>
                    <span className="rounded-md bg-emerald-50 px-2.5 py-1 font-mono text-xs font-medium text-emerald-700">
                      score: {source.score}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-slate-600">{source.reason}</p>
                  {source.chunk_refs.length > 0 ? (
                    <pre className="mt-3 max-h-48 overflow-auto rounded-md bg-slate-950 p-3 text-xs leading-6 text-slate-100">
                      {JSON.stringify(source.chunk_refs, null, 2)}
                    </pre>
                  ) : null}
                </div>
              ))}
            </div>
          </section>
        </section>
      ) : null}
    </main>
  );
}
