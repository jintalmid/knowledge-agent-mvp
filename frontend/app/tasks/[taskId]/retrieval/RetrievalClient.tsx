"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import Pagination from "@/components/Pagination";
import {
  DocumentChunk,
  generateTaskFileChunks,
  getRetrievalSettings,
  getTask,
  getTaskFileChunks,
  getTaskFiles,
  RetrievalMode,
  RetrievalSettings,
  retrieveTaskFiles,
  RetrieveResponse,
  Task,
  TaskFile,
  updateRetrievalSettings,
} from "@/lib/api";
import { usePagination } from "@/lib/usePagination";

const retrievalModes: { value: RetrievalMode; label: string }[] = [
  { value: "summary_only", label: "summary_only" },
  { value: "chunk_text", label: "chunk_text" },
  { value: "embedding", label: "embedding" },
  { value: "hybrid", label: "hybrid" },
];

function previewText(value: string, limit = 120) {
  const normalized = value.replace(/\s+/g, " ").trim();
  if (normalized.length <= limit) {
    return normalized;
  }
  return `${normalized.slice(0, limit)}...`;
}

export default function RetrievalClient({ taskId }: { taskId: string }) {
  const [task, setTask] = useState<Task | null>(null);
  const [taskFiles, setTaskFiles] = useState<TaskFile[]>([]);
  const [settings, setSettings] = useState<RetrievalSettings | null>(null);
  const [chunkCounts, setChunkCounts] = useState<Record<string, number>>({});
  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState<RetrievalMode>("summary_only");
  const [topK, setTopK] = useState(5);
  const [result, setResult] = useState<RetrieveResponse | null>(null);
  const [activeChunkTaskFileId, setActiveChunkTaskFileId] = useState<string | null>(null);
  const [isSavingSettings, setIsSavingSettings] = useState(false);
  const [isRetrieving, setIsRetrieving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setIsLoading(true);
    setError(null);
    try {
      const [loadedTask, loadedFiles, loadedSettings] = await Promise.all([
        getTask(taskId),
        getTaskFiles(taskId),
        getRetrievalSettings(),
      ]);
      setTask(loadedTask);
      setTaskFiles(loadedFiles);
      setSettings(loadedSettings);
      setMode(loadedSettings.retrieval_mode);
      setTopK(loadedSettings.top_k);

      const counts = await Promise.all(
        loadedFiles.map(async (taskFile) => {
          const chunks = await getTaskFileChunks(taskFile.id);
          return [taskFile.id, chunks.length] as const;
        }),
      );
      setChunkCounts(Object.fromEntries(counts));
    } catch (err) {
      setError(err instanceof Error ? err.message : "检索页面加载失败");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, [taskId]);

  async function onGenerateChunks(taskFileId: string) {
    setActiveChunkTaskFileId(taskFileId);
    setError(null);
    try {
      const chunks = await generateTaskFileChunks(taskFileId);
      setChunkCounts((current) => ({ ...current, [taskFileId]: chunks.length }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Chunk 生成失败");
    } finally {
      setActiveChunkTaskFileId(null);
    }
  }

  async function onSaveSettings() {
    setIsSavingSettings(true);
    setError(null);
    try {
      const savedSettings = await updateRetrievalSettings({
        retrieval_mode: mode,
        top_k: topK,
      });
      setSettings(savedSettings);
    } catch (err) {
      setError(err instanceof Error ? err.message : "检索设置保存失败");
    } finally {
      setIsSavingSettings(false);
    }
  }

  async function onRetrieve(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!question.trim()) {
      setError("请输入问题");
      return;
    }

    setIsRetrieving(true);
    setError(null);
    try {
      const response = await retrieveTaskFiles(taskId, {
        question: question.trim(),
        retrieval_mode: mode,
        top_k: topK,
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "检索失败");
    } finally {
      setIsRetrieving(false);
    }
  }

  const chunkableFiles = useMemo(
    () => taskFiles.filter((taskFile) => taskFile.parse_status === "parsed"),
    [taskFiles],
  );
  const taskFilePagination = usePagination(taskFiles, 10);
  const resultPagination = usePagination(result?.results ?? [], 10);

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link className="text-sm font-medium text-slate-600 hover:underline" href={`/tasks/${taskId}`}>
            返回任务详情
          </Link>
          <p className="mt-4 text-sm font-medium text-slate-500">M07 / M08 Retrieval</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">Chunk 与临时检索</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">{task ? task.name : taskId}</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-white" href={`/tasks/${taskId}/summaries`}>
            摘要
          </Link>
          <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-white" href={`/tasks/${taskId}/parsing`}>
            解析
          </Link>
        </div>
      </header>

      {error ? <div className="mb-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
      {isLoading ? <p className="text-sm text-slate-500">加载中</p> : null}

      <section className="mb-6 grid gap-4 rounded-md border border-slate-200 bg-white p-5 shadow-sm md:grid-cols-[1fr_auto]">
        <div className="grid gap-4 md:grid-cols-3">
          <label className="grid gap-1.5">
            <span className="text-sm font-medium text-slate-700">retrieval_mode</span>
            <select
              className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
              onChange={(event) => setMode(event.target.value as RetrievalMode)}
              value={mode}
            >
              {retrievalModes.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1.5">
            <span className="text-sm font-medium text-slate-700">top_k</span>
            <input
              className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
              max={20}
              min={1}
              onChange={(event) => setTopK(Number(event.target.value))}
              type="number"
              value={topK}
            />
          </label>
          <div>
            <p className="text-sm font-medium text-slate-700">当前配置</p>
            <p className="mt-2 font-mono text-xs leading-5 text-slate-500">
              chunk_size: {settings?.chunk_size ?? "-"} / overlap: {settings?.chunk_overlap ?? "-"}
            </p>
          </div>
        </div>
        <button
          className="h-fit rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          disabled={isSavingSettings}
          onClick={onSaveSettings}
          type="button"
        >
          {isSavingSettings ? "保存中" : "保存检索设置"}
        </button>
      </section>

      <section className="mb-6 rounded-md border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-950">Chunk 生成</h2>
            <p className="mt-1 text-sm text-slate-500">仅已解析文件可生成 chunk；embedding 记录本阶段只预留。</p>
          </div>
        </div>
        <div className="grid gap-3">
          {taskFilePagination.paginatedItems.map((taskFile) => {
            const count = chunkCounts[taskFile.id] ?? 0;
            return (
              <div key={taskFile.id} className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-slate-100 p-3">
                <div>
                  <p className="text-sm font-medium text-slate-900">{taskFile.display_name}</p>
                  <p className="mt-1 font-mono text-xs text-slate-500">
                    parse: {taskFile.parse_status} / chunks: {count}
                  </p>
                </div>
                <button
                  className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-400"
                  disabled={activeChunkTaskFileId === taskFile.id || taskFile.parse_status !== "parsed"}
                  onClick={() => onGenerateChunks(taskFile.id)}
                  type="button"
                >
                  {activeChunkTaskFileId === taskFile.id ? "生成中" : count > 0 ? "重新生成 Chunk" : "生成 Chunk"}
                </button>
              </div>
            );
          })}
          {taskFiles.length === 0 ? <p className="text-sm text-slate-500">暂无文件</p> : null}
          {taskFiles.length > 0 && chunkableFiles.length === 0 ? (
            <p className="text-sm text-slate-500">还没有已解析文件，请先进入解析页面。</p>
          ) : null}
        </div>
        {taskFiles.length > 0 ? (
          <Pagination
            label="个文件"
            onPageChange={taskFilePagination.setPage}
            onPageSizeChange={taskFilePagination.setPageSize}
            page={taskFilePagination.page}
            pageSize={taskFilePagination.pageSize}
            totalItems={taskFilePagination.totalItems}
            totalPages={taskFilePagination.totalPages}
          />
        ) : null}
      </section>

      <form className="mb-6 rounded-md border border-slate-200 bg-white p-5 shadow-sm" onSubmit={onRetrieve}>
        <label className="grid gap-1.5">
          <span className="text-sm font-medium text-slate-700">问题</span>
          <textarea
            className="min-h-28 rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
            maxLength={2000}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="输入要筛选相关文件的问题"
            value={question}
          />
        </label>
        <button
          className="mt-4 rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          disabled={isRetrieving}
          type="submit"
        >
          {isRetrieving ? "检索中" : "检索候选文件"}
        </button>
      </form>

      {result ? (
        <section className="grid gap-4">
          <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
            <p className="font-mono text-xs text-slate-500">mode: {result.retrieval_mode} / status: {result.status}</p>
            <p className="mt-2 text-sm text-slate-700">{result.message}</p>
          </div>
          {resultPagination.paginatedItems.map((candidate) => (
            <article key={candidate.task_file_id} className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-slate-950">{candidate.display_name}</h2>
                  <p className="mt-1 break-all font-mono text-xs text-slate-500">{candidate.task_file_id}</p>
                </div>
                <span className="rounded-md bg-emerald-50 px-2.5 py-1 font-mono text-xs font-medium text-emerald-700">
                  score: {candidate.score}
                </span>
              </div>
              <p className="mt-3 text-sm text-slate-700">{candidate.reason}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {candidate.matched_fields.map((field) => (
                  <span key={field} className="rounded-md bg-slate-100 px-2.5 py-1 font-mono text-xs text-slate-600">
                    {field}
                  </span>
                ))}
              </div>
              {candidate.chunk_matches.length > 0 ? (
                <div className="mt-4 grid gap-2">
                  {candidate.chunk_matches.map((chunk) => (
                    <div key={chunk.chunk_id} className="rounded-md bg-slate-50 p-3">
                      <p className="font-mono text-xs text-slate-500">
                        chunk #{chunk.chunk_index} / score {chunk.score}
                      </p>
                      <p className="mt-2 text-sm leading-6 text-slate-700">{previewText(chunk.preview, 260)}</p>
                    </div>
                  ))}
                </div>
              ) : null}
            </article>
          ))}
          {result.results.length === 0 ? <p className="text-sm text-slate-500">暂无候选文件</p> : null}
          {result.results.length > 0 ? (
            <Pagination
              label="个候选"
              onPageChange={resultPagination.setPage}
              onPageSizeChange={resultPagination.setPageSize}
              page={resultPagination.page}
              pageSize={resultPagination.pageSize}
              totalItems={resultPagination.totalItems}
              totalPages={resultPagination.totalPages}
            />
          ) : null}
        </section>
      ) : null}
    </main>
  );
}
