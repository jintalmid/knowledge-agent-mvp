"use client";

import Link from "next/link";
import { DragEvent, FormEvent, useEffect, useRef, useState } from "react";
import Pagination from "@/components/Pagination";
import { deleteTaskFile, getTask, getTaskFiles, parseTaskFile, Task, TaskFile, uploadTaskFile } from "@/lib/api";
import { usePagination } from "@/lib/usePagination";

function formatBytes(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function parseStatusClass(status: string) {
  if (status === "parsed") {
    return "bg-emerald-50 text-emerald-700";
  }
  if (status === "failed") {
    return "bg-red-50 text-red-700";
  }
  if (status === "parsing") {
    return "bg-amber-50 text-amber-700";
  }
  return "bg-slate-100 text-slate-600";
}

export default function TaskFilesClient({ taskId }: { taskId: string }) {
  const [task, setTask] = useState<Task | null>(null);
  const [taskFiles, setTaskFiles] = useState<TaskFile[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadResults, setUploadResults] = useState<Array<{ name: string; status: "success" | "failed"; message?: string }>>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragActive, setIsDragActive] = useState(false);
  const [retryingTaskFileId, setRetryingTaskFileId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const taskFilePagination = usePagination(taskFiles, 10);

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

  function addSelectedFiles(files: FileList | File[]) {
    const incomingFiles = Array.from(files);
    if (incomingFiles.length === 0) {
      return;
    }

    setError(null);
    setUploadResults([]);
    setSelectedFiles((currentFiles) => {
      const knownFiles = new Set(currentFiles.map((file) => `${file.name}:${file.size}:${file.lastModified}`));
      const nextFiles = [...currentFiles];
      for (const file of incomingFiles) {
        const key = `${file.name}:${file.size}:${file.lastModified}`;
        if (!knownFiles.has(key)) {
          nextFiles.push(file);
          knownFiles.add(key);
        }
      }
      return nextFiles;
    });
  }

  function removeSelectedFile(index: number) {
    setSelectedFiles((currentFiles) => currentFiles.filter((_, currentIndex) => currentIndex !== index));
  }

  function clearSelectedFiles() {
    setSelectedFiles([]);
    setUploadResults([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragActive(false);
    addSelectedFiles(event.dataTransfer.files);
  }

  async function onUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedFiles.length === 0) {
      setError("请选择文件");
      return;
    }

    setIsUploading(true);
    setError(null);
    setUploadResults([]);
    const results: Array<{ name: string; status: "success" | "failed"; message?: string }> = [];
    const failedFiles: File[] = [];

    try {
      for (const file of selectedFiles) {
        try {
          await uploadTaskFile(taskId, file);
          results.push({ name: file.name, status: "success" });
        } catch (err) {
          const message = err instanceof Error ? err.message : "文件上传失败";
          failedFiles.push(file);
          results.push({ name: file.name, status: "failed", message });
        }
        setUploadResults([...results]);
      }

      setSelectedFiles(failedFiles);
      if (fileInputRef.current && failedFiles.length === 0) {
        fileInputRef.current.value = "";
      }

      await refresh();

      if (failedFiles.length > 0) {
        setError(`${failedFiles.length} 个文件上传失败，成功的文件已保留并自动解析。`);
      }
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

  async function onRetryParse(taskFileId: string) {
    setRetryingTaskFileId(taskFileId);
    setError(null);
    try {
      await parseTaskFile(taskFileId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "重试解析失败");
      await refresh();
    } finally {
      setRetryingTaskFileId(null);
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
        <form className="mt-4 grid gap-4" onSubmit={onUpload}>
          <div
            className={
              isDragActive
                ? "rounded-md border border-dashed border-slate-500 bg-slate-100 px-5 py-8 text-center"
                : "rounded-md border border-dashed border-slate-300 bg-slate-50 px-5 py-8 text-center"
            }
            onDragEnter={(event) => {
              event.preventDefault();
              setIsDragActive(true);
            }}
            onDragLeave={(event) => {
              event.preventDefault();
              setIsDragActive(false);
            }}
            onDragOver={(event) => {
              event.preventDefault();
              setIsDragActive(true);
            }}
            onDrop={onDrop}
          >
            <p className="text-sm font-medium text-slate-800">拖拽文件到这里上传</p>
            <p className="mt-2 text-xs text-slate-500">也可以一次选择多个文件。支持 txt、md、pdf、csv、xlsx、xls。</p>
            <label
              className="mt-4 inline-flex cursor-pointer rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
              htmlFor="task-file-upload"
            >
              选择文件
            </label>
            <input
              accept=".txt,.md,.pdf,.csv,.xlsx,.xls"
              className="sr-only"
              id="task-file-upload"
              multiple
              onChange={(event) => addSelectedFiles(event.target.files ?? [])}
              ref={fileInputRef}
              type="file"
            />
          </div>

          {selectedFiles.length > 0 ? (
            <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-sm font-medium text-slate-800">待上传文件：{selectedFiles.length} 个</p>
                <button
                  className="text-sm font-medium text-slate-600 hover:text-slate-950"
                  disabled={isUploading}
                  onClick={clearSelectedFiles}
                  type="button"
                >
                  清空
                </button>
              </div>
              <ul className="mt-3 grid gap-2">
                {selectedFiles.map((file, index) => (
                  <li className="flex flex-wrap items-center justify-between gap-3 rounded-md bg-white px-3 py-2 text-sm" key={`${file.name}:${file.size}:${file.lastModified}`}>
                    <span className="min-w-0 truncate text-slate-800">{file.name}</span>
                    <span className="flex items-center gap-3 text-xs text-slate-500">
                      {formatBytes(file.size)}
                      <button
                        className="font-medium text-red-600 hover:text-red-700 disabled:text-slate-400"
                        disabled={isUploading}
                        onClick={() => removeSelectedFile(index)}
                        type="button"
                      >
                        移除
                      </button>
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {uploadResults.length > 0 ? (
            <div className="rounded-md border border-slate-200 bg-white p-3">
              <p className="text-sm font-medium text-slate-800">上传结果</p>
              <ul className="mt-2 grid gap-2">
                {uploadResults.map((result) => (
                  <li className="flex flex-wrap items-center gap-2 text-sm" key={`${result.name}:${result.status}`}>
                    <span className={result.status === "success" ? "text-emerald-700" : "text-red-700"}>
                      {result.status === "success" ? "成功" : "失败"}
                    </span>
                    <span className="text-slate-700">{result.name}</span>
                    {result.message ? <span className="text-xs text-slate-500">{result.message}</span> : null}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <div className="flex flex-wrap items-center gap-3">
            <button
              className="rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
              disabled={isUploading || selectedFiles.length === 0}
              type="submit"
            >
              {isUploading ? "上传中" : `上传 ${selectedFiles.length} 个文件`}
            </button>
          </div>
        </form>
        <p className="mt-3 text-xs text-slate-500">
          上传成功后会自动解析；解析失败时文件仍会保留，可在列表中重试。
        </p>
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
          {taskFilePagination.paginatedItems.map((taskFile) => (
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
                    <span className={`rounded-md px-2.5 py-1 font-mono text-xs font-medium ${parseStatusClass(taskFile.parse_status)}`}>
                      {taskFile.parse_status}
                    </span>
                  </div>

                  <details className="mt-4 rounded-md border border-slate-100 bg-slate-50 px-3 py-2">
                    <summary className="text-sm font-medium text-slate-700">详情</summary>
                    <dl className="mt-3 grid gap-3 text-sm md:grid-cols-3">
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
                  </details>
                  {taskFile.parse_status === "failed" ? (
                    <div className="mt-4 rounded-md border border-red-100 bg-red-50 px-3 py-2 text-sm text-red-700">
                      <p className="font-medium">解析失败</p>
                      <p className="mt-1 line-clamp-2">{taskFile.parse_error || "未记录错误详情"}</p>
                    </div>
                  ) : null}
                </div>
                <div className="flex flex-wrap gap-2">
                  {taskFile.parse_status === "failed" ? (
                    <button
                      className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-400"
                      disabled={retryingTaskFileId === taskFile.id}
                      onClick={() => onRetryParse(taskFile.id)}
                      type="button"
                    >
                      {retryingTaskFileId === taskFile.id ? "解析中" : "重试解析"}
                    </button>
                  ) : null}
                  <button
                    className="rounded-md border border-red-200 px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50"
                    onClick={() => onDelete(taskFile.id)}
                    type="button"
                  >
                    删除引用
                  </button>
                </div>
              </div>
            </article>
          ))}
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
    </main>
  );
}
