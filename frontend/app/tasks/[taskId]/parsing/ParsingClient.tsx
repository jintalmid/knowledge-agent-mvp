"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  getParsedContent,
  getTask,
  getTaskFiles,
  parseAllTaskFiles,
  parseTaskFile,
  ParsedContent,
  Task,
  TaskFile,
} from "@/lib/api";

function previewText(value: string) {
  return value.length > 1600 ? `${value.slice(0, 1600)}\n...` : value;
}

function profileSummary(profile: Record<string, unknown> | null) {
  if (!profile) {
    return "无 profile";
  }
  const sheets = Array.isArray(profile.sheets) ? profile.sheets : [];
  return `${String(profile.format ?? "table")} / ${sheets.length} sheet`;
}

export default function ParsingClient({ taskId }: { taskId: string }) {
  const [task, setTask] = useState<Task | null>(null);
  const [taskFiles, setTaskFiles] = useState<TaskFile[]>([]);
  const [parsedContents, setParsedContents] = useState<Record<string, ParsedContent>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [activeTaskFileId, setActiveTaskFileId] = useState<string | null>(null);
  const [isParsingAll, setIsParsingAll] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadParsedContents(files: TaskFile[]) {
    const entries = await Promise.all(
      files.map(async (file) => {
        try {
          const parsed = await getParsedContent(file.id);
          return [file.id, parsed] as const;
        } catch {
          return null;
        }
      }),
    );
    setParsedContents(Object.fromEntries(entries.filter((entry): entry is readonly [string, ParsedContent] => entry !== null)));
  }

  async function refresh() {
    setIsLoading(true);
    setError(null);
    try {
      const [loadedTask, loadedFiles] = await Promise.all([getTask(taskId), getTaskFiles(taskId)]);
      setTask(loadedTask);
      setTaskFiles(loadedFiles);
      await loadParsedContents(loadedFiles);
    } catch (err) {
      setError(err instanceof Error ? err.message : "解析页面加载失败");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, [taskId]);

  async function onParseOne(taskFileId: string) {
    setActiveTaskFileId(taskFileId);
    setError(null);
    try {
      await parseTaskFile(taskFileId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "单文件解析失败");
      await refresh();
    } finally {
      setActiveTaskFileId(null);
    }
  }

  async function onParseAll() {
    setIsParsingAll(true);
    setError(null);
    try {
      await parseAllTaskFiles(taskId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "批量解析失败");
      await refresh();
    } finally {
      setIsParsingAll(false);
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link className="text-sm font-medium text-slate-600 hover:underline" href={`/tasks/${taskId}`}>
            返回任务详情
          </Link>
          <p className="mt-4 text-sm font-medium text-slate-500">M05 File Parsing</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">文件解析</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">{task ? task.name : taskId}</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link
            className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-white"
            href={`/tasks/${taskId}/files`}
          >
            管理文件
          </Link>
          <button
            className="rounded-md bg-slate-950 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={isParsingAll || taskFiles.length === 0}
            onClick={onParseAll}
            type="button"
          >
            {isParsingAll ? "解析中" : "批量解析"}
          </button>
        </div>
      </header>

      {error ? (
        <div className="mb-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      ) : null}

      {isLoading ? <p className="text-sm text-slate-500">加载中</p> : null}

      {!isLoading && taskFiles.length === 0 ? (
        <div className="rounded-md border border-dashed border-slate-300 bg-white px-4 py-8 text-center text-sm text-slate-500">
          暂无文件，请先进入文件管理页上传。
        </div>
      ) : null}

      <section className="grid gap-4">
        {taskFiles.map((taskFile) => {
          const parsed = parsedContents[taskFile.id];
          return (
            <article key={taskFile.id} className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-3">
                    <h2 className="text-lg font-semibold text-slate-950">{taskFile.display_name}</h2>
                    <span className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                      {taskFile.file_ext}
                    </span>
                    <span className="rounded-md bg-slate-100 px-2.5 py-1 font-mono text-xs font-medium text-slate-600">
                      {taskFile.parse_status}
                    </span>
                  </div>
                  <p className="mt-2 break-all font-mono text-xs text-slate-500">{taskFile.id}</p>
                </div>
                <button
                  className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-400"
                  disabled={activeTaskFileId === taskFile.id || isParsingAll}
                  onClick={() => onParseOne(taskFile.id)}
                  type="button"
                >
                  {activeTaskFileId === taskFile.id ? "解析中" : "解析"}
                </button>
              </div>

              <div className="mt-4 grid gap-3 text-sm md:grid-cols-3">
                <div>
                  <p className="text-xs font-medium text-slate-500">content_type</p>
                  <p className="mt-1 font-mono text-slate-900">{parsed?.content_type ?? "未生成"}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-slate-500">parse_quality</p>
                  <p className="mt-1 font-mono text-slate-900">{parsed?.parse_quality ?? "未生成"}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-slate-500">Excel profile</p>
                  <p className="mt-1 font-mono text-slate-900">{profileSummary(parsed?.excel_profile_json ?? null)}</p>
                </div>
              </div>

              {parsed?.text_content ? (
                <details className="mt-4 rounded-md border border-slate-100 bg-slate-50 p-3">
                  <summary className="text-sm font-semibold text-slate-950">文本预览</summary>
                  <pre className="max-h-96 overflow-auto rounded-md bg-slate-950 p-4 text-xs leading-6 text-slate-100">
                    {previewText(parsed.text_content)}
                  </pre>
                </details>
              ) : null}

              {parsed?.excel_profile_json ? (
                <details className="mt-4 rounded-md border border-slate-100 bg-slate-50 p-3">
                  <summary className="text-sm font-semibold text-slate-950">Excel profile 预览</summary>
                  <pre className="max-h-96 overflow-auto rounded-md bg-slate-950 p-4 text-xs leading-6 text-slate-100">
                    {JSON.stringify(parsed.excel_profile_json, null, 2)}
                  </pre>
                </details>
              ) : null}
            </article>
          );
        })}
      </section>
    </main>
  );
}
