"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Pagination from "@/components/Pagination";
import { Answer, askTaskQuestion, getTaskResults, startAgentRun } from "@/lib/api";
import { copyText } from "@/lib/clipboard";
import { usePagination } from "@/lib/usePagination";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function extractUncertainties(markdown: string) {
  const keywords = ["不确定", "缺失", "未提供", "无法", "不足", "uncertain", "missing", "insufficient", "not enough", "cannot determine"];
  return markdown
    .split(/\n+/)
    .map((line) => line.replace(/^[-*#\s]+/, "").trim())
    .filter((line) => line && keywords.some((keyword) => line.toLowerCase().includes(keyword)));
}

export default function ResultsClient({ taskId }: { taskId: string }) {
  const router = useRouter();
  const [results, setResults] = useState<Answer[]>([]);
  const [activeAnswerId, setActiveAnswerId] = useState<string | null>(null);
  const [copiedAnswerId, setCopiedAnswerId] = useState<string | null>(null);
  const [rerunningAnswerId, setRerunningAnswerId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setIsLoading(true);
    setError(null);
    try {
      const loadedResults = await getTaskResults(taskId);
      setResults(loadedResults);
      setActiveAnswerId((current) => current ?? loadedResults[0]?.id ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "历史结果加载失败");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, [taskId]);

  async function onCopy(answer: Answer) {
    try {
      await copyText(answer.answer_text_markdown);
      setCopiedAnswerId(answer.id);
      window.setTimeout(() => setCopiedAnswerId(null), 1600);
    } catch (err) {
      setError(err instanceof Error ? err.message : "复制失败");
    }
  }

  async function onRerun(answer: Answer) {
    if (answer.agent_run_id) {
      setRerunningAnswerId(answer.id);
      setError(null);
      try {
        const response = await startAgentRun(taskId, {
          question: answer.question_text,
          max_iterations: Math.min(Math.max(answer.iteration_count || 10, 1), 10),
        });
        router.push(`/tasks/${taskId}/runs/${response.agent_run_id}`);
      } catch (err) {
        setError(err instanceof Error ? err.message : "重新运行 Agent Run 失败");
      } finally {
        setRerunningAnswerId(null);
      }
      return;
    }

    if (answer.question_type !== "text_qa") {
      setError("当前只支持重新运行文本问答结果；Excel 分析请回到 Excel 页面重新执行。");
      return;
    }

    setRerunningAnswerId(answer.id);
    setError(null);
    try {
      const newAnswer = await askTaskQuestion(taskId, answer.question_text);
      const loadedResults = await getTaskResults(taskId);
      setResults(loadedResults);
      setActiveAnswerId(newAnswer.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "重新运行失败");
    } finally {
      setRerunningAnswerId(null);
    }
  }

  const activeAnswer = results.find((answer) => answer.id === activeAnswerId) ?? null;
  const uncertainties = activeAnswer ? extractUncertainties(activeAnswer.answer_text_markdown) : [];
  const resultPagination = usePagination(results, 10);

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link className="text-sm font-medium text-slate-600 hover:underline" href={`/tasks/${taskId}`}>
            返回任务详情
          </Link>
          <p className="mt-4 text-sm font-medium text-slate-500">M11 Result Source View</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">结果与来源</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">当前展示文本问答结果和来源文件。</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-white" href={`/tasks/${taskId}/ask`}>
            文本问答
          </Link>
          <Link className="rounded-md bg-slate-950 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800" href={`/tasks/${taskId}/agent`}>
            Agent Run
          </Link>
        </div>
      </header>

      {error ? <div className="mb-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
      {isLoading ? <p className="text-sm text-slate-500">加载中</p> : null}

      <section className="grid gap-4 lg:grid-cols-[320px_1fr]">
        <aside className="grid h-fit gap-3">
          {resultPagination.paginatedItems.map((answer) => (
            <button
              className={
                activeAnswerId === answer.id
                  ? "rounded-md border border-slate-950 bg-white p-4 text-left shadow-sm"
                  : "rounded-md border border-slate-200 bg-white p-4 text-left shadow-sm hover:border-slate-300"
              }
              key={answer.id}
              onClick={() => setActiveAnswerId(answer.id)}
              type="button"
            >
              <p className="line-clamp-2 text-sm font-medium text-slate-950">{answer.question_text}</p>
              <p className="mt-2 text-xs text-slate-500">{formatDate(answer.created_at)}</p>
              <p className="mt-2 font-mono text-xs text-slate-500">{answer.source_refs_json.length} sources</p>
            </button>
          ))}
          {results.length === 0 && !isLoading ? <p className="text-sm text-slate-500">暂无历史结果</p> : null}
          {results.length > 0 ? (
            <Pagination
              label="条结果"
              onPageChange={resultPagination.setPage}
              onPageSizeChange={resultPagination.setPageSize}
              page={resultPagination.page}
              pageSize={resultPagination.pageSize}
              totalItems={resultPagination.totalItems}
              totalPages={resultPagination.totalPages}
            />
          ) : null}
        </aside>

        {activeAnswer ? (
          <article className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-slate-500">{formatDate(activeAnswer.created_at)}</p>
                <h2 className="mt-1 text-lg font-semibold text-slate-950">{activeAnswer.question_text}</h2>
                {activeAnswer.agent_run_id ? (
                  <Link
                    className="mt-2 inline-block font-mono text-xs text-slate-500 hover:underline"
                    href={`/tasks/${taskId}/runs/${activeAnswer.agent_run_id}`}
                  >
                    {activeAnswer.agent_run_id}
                  </Link>
                ) : null}
              </div>
              <div className="flex flex-wrap gap-3">
                <button
                  className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-400"
                  disabled={rerunningAnswerId === activeAnswer.id}
                  onClick={() => onRerun(activeAnswer)}
                  type="button"
                >
                  {rerunningAnswerId === activeAnswer.id ? "运行中" : "重新运行"}
                </button>
                <button
                  className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                  onClick={() => onCopy(activeAnswer)}
                  type="button"
                >
                  {copiedAnswerId === activeAnswer.id ? "已复制" : "复制 Markdown"}
                </button>
              </div>
            </div>
            <div className="whitespace-pre-wrap rounded-md bg-slate-50 p-4 text-sm leading-7 text-slate-800">
              {activeAnswer.answer_text_markdown}
            </div>
            <p className="mt-3 font-mono text-xs text-slate-500">
              {activeAnswer.llm_provider} / {activeAnswer.llm_model} / iteration {activeAnswer.iteration_count}
            </p>

            <section className="mt-6">
              <h3 className="text-base font-semibold text-slate-950">Used files</h3>
              <div className="mt-3 grid gap-3">
                {activeAnswer.source_refs_json.map((source) => (
                  <div key={source.task_file_id} className="rounded-md border border-slate-100 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-medium text-slate-900">{source.display_name}</p>
                        <p className="mt-1 break-all font-mono text-xs text-slate-500">{source.physical_file_id}</p>
                      </div>
                      <span className="rounded-md bg-emerald-50 px-2.5 py-1 font-mono text-xs font-medium text-emerald-700">
                        score: {source.score}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-600">{source.reason}</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {source.matched_fields.map((field) => (
                        <span key={field} className="rounded-md bg-slate-100 px-2.5 py-1 font-mono text-xs text-slate-600">
                          {field}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
                {activeAnswer.source_refs_json.length === 0 ? (
                  <p className="text-sm text-slate-500">暂无来源文件记录</p>
                ) : null}
              </div>
            </section>

            <section className="mt-6">
              <h3 className="text-base font-semibold text-slate-950">Uncertainties</h3>
              <div className="mt-3 rounded-md border border-slate-100 bg-slate-50 p-3">
                {uncertainties.length > 0 ? (
                  <ul className="grid gap-2 text-sm leading-6 text-slate-700">
                    {uncertainties.map((line) => (
                      <li key={line}>{line}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-500">未检测到明确不确定性表述。</p>
                )}
              </div>
            </section>
          </article>
        ) : null}
      </section>
    </main>
  );
}
