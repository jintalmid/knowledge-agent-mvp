"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import Pagination from "@/components/Pagination";
import { AgentRun, getAgentRun } from "@/lib/api";
import { usePagination } from "@/lib/usePagination";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function stringValue(value: unknown, fallback = "") {
  return typeof value === "string" ? value : fallback;
}

function stringList(value: unknown) {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((item) => String(item)).filter(Boolean);
}

function resultsHref(taskId: string, answerId: string | null | undefined) {
  return answerId ? `/tasks/${taskId}/results?answerId=${answerId}` : `/tasks/${taskId}/results`;
}

function JsonBlock({ value }: { value: unknown }) {
  return (
    <details className="mt-3 rounded-md border border-slate-200 bg-white p-3">
      <summary className="text-xs font-medium text-slate-600">查看原始 JSON</summary>
      <pre className="mt-3 max-h-80 overflow-auto rounded-md bg-slate-950 p-3 text-xs leading-6 text-slate-100">
        {JSON.stringify(value, null, 2)}
      </pre>
    </details>
  );
}

export default function AgentRunClient({ taskId, runId }: { taskId: string; runId: string }) {
  const [agentRun, setAgentRun] = useState<AgentRun | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const iterationPagination = usePagination(agentRun?.iterations ?? [], 10);

  async function refresh() {
    setIsLoading(true);
    setError(null);
    try {
      setAgentRun(await getAgentRun(runId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Agent Run 加载失败");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, [runId]);

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link className="text-sm font-medium text-slate-600 hover:underline" href={`/tasks/${taskId}`}>
            返回任务详情
          </Link>
          <p className="mt-4 text-sm font-medium text-slate-500">Agent Run Detail</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">运行过程</h1>
          <p className="mt-3 break-all font-mono text-xs text-slate-500">{runId}</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link
            className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-white"
            href={`/tasks/${taskId}/agent`}
          >
            新 Agent Run
          </Link>
          <Link
            className="rounded-md bg-slate-950 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800"
            href={resultsHref(taskId, agentRun?.answer_id)}
          >
            查看结果
          </Link>
        </div>
      </header>

      {error ? <div className="mb-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
      {isLoading ? <p className="text-sm text-slate-500">加载中</p> : null}

      {agentRun ? (
        <section className="grid gap-5">
          <article className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <div className="grid gap-4 md:grid-cols-4">
              <div>
                <p className="text-xs font-medium text-slate-500">status</p>
                <p className="mt-1 font-mono text-sm text-slate-950">{agentRun.status}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500">iteration</p>
                <p className="mt-1 font-mono text-sm text-slate-950">
                  {agentRun.current_iteration} / {agentRun.max_iterations}
                </p>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500">stop reason</p>
                <p className="mt-1 font-mono text-sm text-slate-950">{agentRun.stop_reason ?? "-"}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500">created</p>
                <p className="mt-1 text-sm text-slate-950">{formatDate(agentRun.created_at)}</p>
              </div>
            </div>
            <h2 className="mt-5 text-lg font-semibold text-slate-950">问题</h2>
            <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">{agentRun.goal}</p>
          </article>

          {agentRun.final_answer_markdown ? (
            <article className="rounded-md border border-emerald-200 bg-white p-5 shadow-sm">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-emerald-700">Final Answer</p>
                  <h2 className="mt-1 text-lg font-semibold text-slate-950">任务结果</h2>
                </div>
                <Link
                  className="rounded-md bg-slate-950 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800"
                  href={resultsHref(taskId, agentRun.answer_id)}
                >
                  查看历史结果
                </Link>
              </div>
              <div className="mt-3 whitespace-pre-wrap rounded-md bg-emerald-50 p-4 text-sm leading-7 text-slate-800">
                {agentRun.final_answer_markdown}
              </div>
              <p className="mt-3 font-mono text-xs text-slate-500">
                {agentRun.answer_id ? `已保存到历史结果：${agentRun.answer_id}` : "尚未找到对应的历史结果记录"}
              </p>
            </article>
          ) : (
            <article className="rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
              这个 Agent Run 还没有最终答案。可以查看下方每轮过程定位卡在哪一步。
            </article>
          )}

          {iterationPagination.paginatedItems.map((iteration) => {
            const plan = iteration.plan_text ?? {};
            const reflection = iteration.reflection_text ?? {};
            const selectedFiles = stringList(plan.selected_file_ids);
            return (
              <article className="rounded-md border border-slate-200 bg-white p-5 shadow-sm" key={iteration.id}>
                <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-slate-500">Iteration {iteration.iteration_index}</p>
                    <p className="mt-1 break-all font-mono text-xs text-slate-400">{iteration.id}</p>
                    <h2 className="mt-1 text-lg font-semibold text-slate-950">
                      {stringValue(plan.selected_tool, iteration.tool_name ?? "未选择工具")}
                    </h2>
                  </div>
                  <span className="rounded-md bg-slate-100 px-2.5 py-1 font-mono text-xs text-slate-700">
                    {iteration.status} / {iteration.decision}
                  </span>
                </div>

                <details className="mb-4 rounded-md border border-slate-100 bg-slate-50 p-3">
                  <summary className="text-sm font-medium text-slate-700">thought</summary>
                  <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">
                    {stringValue(plan.thought, "未记录 thought")}
                  </p>
                </details>

                <div className="grid gap-4 lg:grid-cols-2">
                  <section className="rounded-md border border-slate-100 p-4">
                    <h3 className="text-sm font-semibold text-slate-950">Plan</h3>
                    <dl className="mt-3 grid gap-3 text-sm">
                      <div>
                        <dt className="font-medium text-slate-500">selected files</dt>
                        <dd className="mt-1 flex flex-wrap gap-2">
                          {selectedFiles.length > 0 ? (
                            selectedFiles.map((fileId) => (
                              <span className="rounded-md bg-slate-100 px-2.5 py-1 font-mono text-xs text-slate-700" key={fileId}>
                                {fileId}
                              </span>
                            ))
                          ) : (
                            <span className="text-slate-500">无</span>
                          )}
                        </dd>
                      </div>
                      <div>
                        <dt className="font-medium text-slate-500">selected tool</dt>
                        <dd className="mt-1 font-mono text-slate-900">{stringValue(plan.selected_tool, iteration.tool_name ?? "-")}</dd>
                      </div>
                      <div>
                        <dt className="font-medium text-slate-500">instruction</dt>
                        <dd className="mt-1 whitespace-pre-wrap text-slate-700">{stringValue(plan.tool_instruction, "-")}</dd>
                      </div>
                      <div>
                        <dt className="font-medium text-slate-500">reason</dt>
                        <dd className="mt-1 whitespace-pre-wrap text-slate-700">{stringValue(plan.reason, "-")}</dd>
                      </div>
                    </dl>
                  </section>

                  <section className="rounded-md border border-slate-100 p-4">
                    <h3 className="text-sm font-semibold text-slate-950">Reflection</h3>
                    <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-700">
                      {stringValue(reflection.reflection, "未记录 reflection")}
                    </p>
                    <dl className="mt-3 grid gap-2 text-sm">
                      <div>
                        <dt className="font-medium text-slate-500">decision</dt>
                        <dd className="mt-1 font-mono text-slate-900">{stringValue(reflection.decision, iteration.decision)}</dd>
                      </div>
                      <div>
                        <dt className="font-medium text-slate-500">missing information</dt>
                        <dd className="mt-1 text-slate-700">
                          {stringList(reflection.missing_information).join("；") || "无明确缺失信息"}
                        </dd>
                      </div>
                      <div>
                        <dt className="font-medium text-slate-500">next step hint</dt>
                        <dd className="mt-1 text-slate-700">{stringValue(reflection.next_step_hint, "-")}</dd>
                      </div>
                    </dl>
                  </section>
                </div>

                <section className="mt-4 rounded-md border border-slate-100 p-4">
                  <h3 className="text-sm font-semibold text-slate-950">Observation</h3>
                  <div className="mt-3 grid gap-3">
                    {iteration.observations.map((observation, observationIndex) => (
                      <div className="rounded-md bg-slate-50 p-3" key={observation.id}>
                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <div>
                            <p className="font-mono text-xs font-medium text-slate-700">
                              Observation {iteration.iteration_index}.{observationIndex + 1}
                            </p>
                            <p className="mt-1 break-all font-mono text-xs text-slate-500">
                              {observation.id} / {observation.tool_name} / {observation.status}
                            </p>
                          </div>
                          <p className="text-xs text-slate-500">{formatDate(observation.created_at)}</p>
                        </div>
                        <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-800">
                          {observation.content_text ?? "无 observation 文本"}
                        </p>
                        {observation.error_message ? (
                          <p className="mt-2 text-sm text-red-700">{observation.error_message}</p>
                        ) : null}
                        <JsonBlock value={observation.content_json} />
                      </div>
                    ))}
                    {iteration.observations.length === 0 ? <p className="text-sm text-slate-500">暂无 observation</p> : null}
                  </div>
                </section>
              </article>
            );
          })}
          {agentRun.iterations.length > 0 ? (
            <Pagination
              label="轮迭代"
              onPageChange={iterationPagination.setPage}
              onPageSizeChange={iterationPagination.setPageSize}
              page={iterationPagination.page}
              pageSize={iterationPagination.pageSize}
              totalItems={iterationPagination.totalItems}
              totalPages={iterationPagination.totalPages}
            />
          ) : null}

        </section>
      ) : null}
    </main>
  );
}
