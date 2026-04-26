"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  FileSummary,
  getTask,
  getTaskFiles,
  getTaskSummaries,
  summarizeAllTaskFiles,
  summarizeTaskFile,
  Task,
  TaskFile,
} from "@/lib/api";

export default function SummariesClient({ taskId }: { taskId: string }) {
  const [task, setTask] = useState<Task | null>(null);
  const [taskFiles, setTaskFiles] = useState<TaskFile[]>([]);
  const [summaries, setSummaries] = useState<FileSummary[]>([]);
  const [activeTaskFileId, setActiveTaskFileId] = useState<string | null>(null);
  const [isSummarizingAll, setIsSummarizingAll] = useState(false);
  const [isSummarizingMissing, setIsSummarizingMissing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setIsLoading(true);
    setError(null);
    try {
      const [loadedTask, loadedFiles, loadedSummaries] = await Promise.all([
        getTask(taskId),
        getTaskFiles(taskId),
        getTaskSummaries(taskId),
      ]);
      setTask(loadedTask);
      setTaskFiles(loadedFiles);
      setSummaries(loadedSummaries);
    } catch (err) {
      setError(err instanceof Error ? err.message : "摘要页面加载失败");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, [taskId]);

  async function onSummarizeOne(taskFileId: string) {
    setActiveTaskFileId(taskFileId);
    setError(null);
    try {
      await summarizeTaskFile(taskFileId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "单文件摘要失败");
      await refresh();
    } finally {
      setActiveTaskFileId(null);
    }
  }

  async function onSummarizeMissing() {
    const summarizedTaskFileIds = new Set(summaries.map((summary) => summary.task_file_id));
    const missingSummaryFiles = taskFiles.filter((taskFile) => !summarizedTaskFileIds.has(taskFile.id));
    if (missingSummaryFiles.length === 0) {
      return;
    }

    setIsSummarizingMissing(true);
    setError(null);
    try {
      for (const taskFile of missingSummaryFiles) {
        await summarizeTaskFile(taskFile.id);
      }
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "批量生成未生成摘要失败");
      await refresh();
    } finally {
      setIsSummarizingMissing(false);
    }
  }

  async function onSummarizeAll() {
    setIsSummarizingAll(true);
    setError(null);
    try {
      await summarizeAllTaskFiles(taskId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "批量摘要失败");
      await refresh();
    } finally {
      setIsSummarizingAll(false);
    }
  }

  const summaryByTaskFile = Object.fromEntries(summaries.map((summary) => [summary.task_file_id, summary]));
  const missingSummaryCount = taskFiles.filter((taskFile) => !summaryByTaskFile[taskFile.id]).length;
  const isBatchSummarizing = isSummarizingAll || isSummarizingMissing;

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link className="text-sm font-medium text-slate-600 hover:underline" href={`/tasks/${taskId}`}>
            返回任务详情
          </Link>
          <p className="mt-4 text-sm font-medium text-slate-500">M06 Summary Tagging</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">摘要与标签</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">{task ? task.name : taskId}</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-white" href="/settings/llm">
            LLM 设置
          </Link>
          <button
            className="rounded-md bg-slate-950 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={isBatchSummarizing || missingSummaryCount === 0}
            onClick={onSummarizeMissing}
            type="button"
          >
            {isSummarizingMissing ? "生成中" : "仅生成未生成"}
          </button>
          <button
            className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-white disabled:cursor-not-allowed disabled:text-slate-400"
            disabled={isBatchSummarizing || taskFiles.length === 0}
            onClick={onSummarizeAll}
            type="button"
          >
            {isSummarizingAll ? "生成中" : "全部重新生成"}
          </button>
        </div>
      </header>

      {error ? <div className="mb-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
      {isLoading ? <p className="text-sm text-slate-500">加载中</p> : null}

      <section className="grid gap-4">
        {taskFiles.map((taskFile) => {
          const summary = summaryByTaskFile[taskFile.id];
          return (
            <article key={taskFile.id} className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="flex flex-wrap items-center gap-3">
                    <h2 className="text-lg font-semibold text-slate-950">{taskFile.display_name}</h2>
                    <span className="rounded-md bg-slate-100 px-2.5 py-1 font-mono text-xs font-medium text-slate-600">
                      parse: {taskFile.parse_status}
                    </span>
                    <span className="rounded-md bg-slate-100 px-2.5 py-1 font-mono text-xs font-medium text-slate-600">
                      summary: {taskFile.summary_status}
                    </span>
                  </div>
                  <p className="mt-2 break-all font-mono text-xs text-slate-500">{taskFile.id}</p>
                </div>
                <button
                  className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-400"
                  disabled={activeTaskFileId === taskFile.id || isBatchSummarizing}
                  onClick={() => onSummarizeOne(taskFile.id)}
                  type="button"
                >
                  {activeTaskFileId === taskFile.id ? "生成中" : summary ? "重新生成" : "生成摘要"}
                </button>
              </div>

              {summary ? (
                <div className="mt-4 grid gap-4">
                  <p className="text-sm leading-6 text-slate-700">{summary.summary_text}</p>
                  <div className="flex flex-wrap gap-2">
                    {[summary.category, ...summary.tags_json].map((tag) => (
                      <span key={tag} className="rounded-md bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
                        {tag}
                      </span>
                    ))}
                  </div>
                  <p className="font-mono text-xs text-slate-500">
                    {summary.llm_provider} / {summary.llm_model}
                  </p>
                  {summary.table_understanding ? (
                    <pre className="max-h-80 overflow-auto rounded-md bg-slate-950 p-4 text-xs leading-6 text-slate-100">
                      {JSON.stringify(summary.table_understanding, null, 2)}
                    </pre>
                  ) : null}
                </div>
              ) : (
                <p className="mt-4 text-sm text-slate-500">暂无摘要</p>
              )}
            </article>
          );
        })}
      </section>
    </main>
  );
}
