"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { deleteTaskFile, getTask, getTaskFiles, Task, TaskFile, uploadTaskFile } from "@/lib/api";

function formatBytes(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export default function TaskFilesClient({ taskId }: { taskId: string }) {
  const [task, setTask] = useState<Task | null>(null);
  const [taskFiles, setTaskFiles] = useState<TaskFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setIsLoading(true);
    setError(null);
    try {
      const [loadedTask, loadedFiles] = await Promise.all([getTask(taskId), getTaskFiles(taskId)]);
      setTask(loadedTask);
      setTaskFiles(loadedFiles);
    } catch (err) {
      setError(err instanceof Error ? err.message : "文件列表加载失败");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, [taskId]);

  async function onUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!selectedFile) {
      setError("请选择文件");
      return;
    }

    setIsUploading(true);
    setError(null);
    try {
      await uploadTaskFile(taskId, selectedFile);
      setSelectedFile(null);
      form.reset();
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "文件上传失败");
    } finally {
      setIsUploading(false);
    }
  }

  async function onDelete(taskFileId: string) {
    setError(null);
    try {
      await deleteTaskFile(taskFileId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "文件引用删除失败");
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link className="text-sm font-medium text-slate-600 hover:underline" href={`/tasks/${taskId}`}>
            返回任务详情
          </Link>
          <p className="mt-4 text-sm font-medium text-slate-500">M03 / M04</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">任务文件</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
            {task ? task.name : taskId}
          </p>
        </div>
      </header>

      {error ? (
        <div className="mb-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      ) : null}

      <section className="mb-8 rounded-md border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-950">上传文件</h2>
        <form className="mt-4 flex flex-wrap items-end gap-3" onSubmit={onUpload}>
          <label className="grid min-w-72 gap-1.5">
            <span className="text-sm font-medium text-slate-700">文件</span>
            <input
              accept=".txt,.md,.csv,.xlsx,.xls"
              className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
              onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
              type="file"
            />
          </label>
          <button
            className="rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={isUploading}
            type="submit"
          >
            {isUploading ? "上传中" : "上传"}
          </button>
        </form>
        <p className="mt-3 text-xs text-slate-500">支持 txt、md、csv、xlsx、xls。当前只建立文件资产与引用，不执行解析。</p>
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-950">文件引用</h2>
          <span className="text-sm text-slate-500">{taskFiles.length} 个文件</span>
        </div>

        {isLoading ? <p className="text-sm text-slate-500">加载中</p> : null}

        {!isLoading && taskFiles.length === 0 ? (
          <div className="rounded-md border border-dashed border-slate-300 bg-white px-4 py-8 text-center text-sm text-slate-500">
            暂无任务文件
          </div>
        ) : null}

        <div className="grid gap-3">
          {taskFiles.map((taskFile) => (
            <article key={taskFile.id} className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-3">
                    <h3 className="text-lg font-semibold text-slate-950">{taskFile.display_name}</h3>
                    <span className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                      {taskFile.file_ext}
                    </span>
                    <span
                      className={
                        taskFile.reused_existing_file
                          ? "rounded-md bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700"
                          : "rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600"
                      }
                    >
                      {taskFile.reused_existing_file ? "复用已有文件" : "新物理文件"}
                    </span>
                  </div>

                  <dl className="mt-4 grid gap-3 text-sm md:grid-cols-3">
                    <div>
                      <dt className="text-xs font-medium text-slate-500">parse_status</dt>
                      <dd className="mt-1 font-mono text-slate-900">{taskFile.parse_status}</dd>
                    </div>
                    <div>
                      <dt className="text-xs font-medium text-slate-500">summary_status</dt>
                      <dd className="mt-1 font-mono text-slate-900">{taskFile.summary_status}</dd>
                    </div>
                    <div>
                      <dt className="text-xs font-medium text-slate-500">embedding_status</dt>
                      <dd className="mt-1 font-mono text-slate-900">{taskFile.embedding_status}</dd>
                    </div>
                    <div>
                      <dt className="text-xs font-medium text-slate-500">physical_file_id</dt>
                      <dd className="mt-1 break-all font-mono text-slate-900">{taskFile.physical_file_id}</dd>
                    </div>
                    <div>
                      <dt className="text-xs font-medium text-slate-500">ref_count</dt>
                      <dd className="mt-1 font-mono text-slate-900">{taskFile.ref_count}</dd>
                    </div>
                    <div>
                      <dt className="text-xs font-medium text-slate-500">文件大小</dt>
                      <dd className="mt-1 text-slate-900">{formatBytes(taskFile.file_size)}</dd>
                    </div>
                  </dl>
                </div>
                <button
                  className="rounded-md border border-red-200 px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50"
                  onClick={() => onDelete(taskFile.id)}
                  type="button"
                >
                  删除引用
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
