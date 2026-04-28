"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";
import Pagination from "@/components/Pagination";
import { createTask, deleteTask, getTasks, Task } from "@/lib/api";
import { usePagination } from "@/lib/usePagination";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function statusClass(status: string) {
  if (status === "active") {
    return "bg-emerald-50 text-emerald-700";
  }
  if (status === "archived") {
    return "bg-slate-200 text-slate-600";
  }
  return "bg-slate-100 text-slate-700";
}

export default function TasksClient() {
  const router = useRouter();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deletingTaskId, setDeletingTaskId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const activeCount = useMemo(() => tasks.filter((task) => task.status === "active").length, [tasks]);
  const draftCount = useMemo(() => tasks.filter((task) => task.status === "draft").length, [tasks]);
  const taskPagination = usePagination(tasks, 10);

  async function refreshTasks() {
    setIsLoading(true);
    setError(null);
    try {
      setTasks(await getTasks());
    } catch (err) {
      setError(err instanceof Error ? err.message : "任务列表加载失败");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    refreshTasks();
  }, []);

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!name.trim()) {
      setError("任务名称不能为空");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      const task = await createTask({
        name: name.trim(),
        description: description.trim(),
      });
      setName("");
      setDescription("");
      await refreshTasks();
      router.push(`/tasks/${task.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "任务创建失败");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function onDelete(taskId: string) {
    setDeletingTaskId(taskId);
    setError(null);
    try {
      await deleteTask(taskId);
      await refreshTasks();
    } catch (err) {
      setError(err instanceof Error ? err.message : "任务删除失败");
    } finally {
      setDeletingTaskId(null);
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-7xl py-8 lg:py-10">
      <header className="mb-6 overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 bg-slate-50 px-5 py-3">
          <p className="text-sm font-medium text-slate-500">M02 Agent Workspace</p>
        </div>
        <div className="p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="mt-2 text-3xl font-semibold text-slate-950">任务空间</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              任务是 Agent 的临时工作区。上传文件后会自动解析，随后可以直接启动 Agent Run。
            </p>
          </div>
          <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50" href="/modules">
            模块地图
          </Link>
        </div>
        </div>
      </header>

      {error ? (
        <div className="mb-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      ) : null}

      <section className="mb-5 grid gap-4 md:grid-cols-3">
        <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">全部任务</p>
          <p className="mt-2 text-2xl font-semibold text-slate-950">{tasks.length}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">草稿</p>
          <p className="mt-2 text-2xl font-semibold text-slate-950">{draftCount}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">Active</p>
          <p className="mt-2 text-2xl font-semibold text-slate-950">{activeCount}</p>
        </div>
      </section>

      <section className="grid gap-5 xl:grid-cols-[360px_1fr]">
        <aside className="h-fit rounded-md border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-950">创建任务</h2>
          <p className="mt-1 text-sm leading-6 text-slate-500">创建后会直接进入任务总览。</p>
          <form className="mt-4 grid gap-4" onSubmit={onCreate}>
            <label className="grid gap-1.5">
              <span className="text-sm font-medium text-slate-700">名称</span>
              <input
                className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
                maxLength={120}
                onChange={(event) => setName(event.target.value)}
                placeholder="例如：9月供应商业绩分析"
                value={name}
              />
            </label>
            <label className="grid gap-1.5">
              <span className="text-sm font-medium text-slate-700">描述</span>
              <textarea
                className="min-h-24 rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
                maxLength={2000}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="记录本次分析目标、文件范围或注意事项"
                value={description}
              />
            </label>
            <button
              className="rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
              disabled={isSubmitting}
              type="submit"
            >
              {isSubmitting ? "创建中" : "创建并进入任务"}
            </button>
          </form>
        </aside>

        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-950">最近任务</h2>
            <span className="text-sm text-slate-500">{tasks.length} 个</span>
          </div>

          {isLoading ? <p className="text-sm text-slate-500">加载中</p> : null}

          {!isLoading && tasks.length === 0 ? (
            <div className="rounded-md border border-dashed border-slate-300 bg-white px-4 py-10 text-center text-sm text-slate-500">
              暂无任务。创建一个任务后即可上传文件并启动 Agent。
            </div>
          ) : null}

          <div className="grid gap-3">
            {taskPagination.paginatedItems.map((task) => (
              <article key={task.id} className="rounded-md border border-slate-200 bg-white p-4 shadow-sm hover:border-slate-300 hover:shadow-md">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-3">
                      <Link className="text-lg font-semibold text-slate-950 hover:underline" href={`/tasks/${task.id}`}>
                        {task.name}
                      </Link>
                      <span className={`rounded-md px-2.5 py-1 text-xs font-medium ${statusClass(task.status)}`}>{task.status}</span>
                    </div>
                    <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-600">{task.description || "无描述"}</p>
                    <p className="mt-2 text-xs text-slate-500">{formatDate(task.created_at)}</p>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Link className="rounded-md bg-slate-950 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800" href={`/tasks/${task.id}`}>
                      打开
                    </Link>
                    <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50" href={`/tasks/${task.id}/files`}>
                      文件
                    </Link>
                    <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50" href={`/tasks/${task.id}/agent`}>
                      Agent
                    </Link>
                    <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50" href={`/tasks/${task.id}/results`}>
                      结果
                    </Link>
                  </div>
                </div>

                <details className="mt-4 rounded-md border border-slate-100 bg-slate-50 px-3 py-2">
                  <summary className="text-sm font-medium text-slate-700">详情与危险操作</summary>
                  <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
                    <div className="flex flex-wrap gap-x-5 gap-y-2 font-mono text-xs text-slate-500">
                      <span>{task.id}</span>
                      <span>{task.owner_user_id}</span>
                      <span>{task.department_id}</span>
                      <span>{task.security_level}</span>
                    </div>
                    <button
                      className="rounded-md border border-red-200 px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:text-red-300"
                      disabled={deletingTaskId === task.id}
                      onClick={() => onDelete(task.id)}
                      type="button"
                    >
                      {deletingTaskId === task.id ? "删除中" : "删除任务"}
                    </button>
                  </div>
                </details>
              </article>
            ))}
          </div>
          {tasks.length > 0 ? (
            <Pagination
              label="个任务"
              onPageChange={taskPagination.setPage}
              onPageSizeChange={taskPagination.setPageSize}
              page={taskPagination.page}
              pageSize={taskPagination.pageSize}
              totalItems={taskPagination.totalItems}
              totalPages={taskPagination.totalPages}
            />
          ) : null}
        </section>
      </section>
    </main>
  );
}
