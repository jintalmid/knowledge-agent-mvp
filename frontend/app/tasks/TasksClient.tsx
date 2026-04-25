"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { createTask, deleteTask, getTasks, Task } from "@/lib/api";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function TasksClient() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      await createTask({
        name: name.trim(),
        description: description.trim(),
      });
      setName("");
      setDescription("");
      await refreshTasks();
    } catch (err) {
      setError(err instanceof Error ? err.message : "任务创建失败");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function onDelete(taskId: string) {
    setError(null);
    try {
      await deleteTask(taskId);
      await refreshTasks();
    } catch (err) {
      setError(err instanceof Error ? err.message : "任务删除失败");
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">M02 Task Workspace</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">任务空间</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
            当前阶段只创建临时任务空间，并预留默认身份、部门、安全等级和后续知识库/模板字段。
          </p>
        </div>
        <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-white" href="/modules">
          模块列表
        </Link>
      </header>

      {error ? (
        <div className="mb-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      ) : null}

      <section className="mb-8 rounded-md border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-950">创建任务</h2>
        <form className="mt-4 grid gap-4" onSubmit={onCreate}>
          <label className="grid gap-1.5">
            <span className="text-sm font-medium text-slate-700">名称</span>
            <input
              className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
              maxLength={120}
              onChange={(event) => setName(event.target.value)}
              placeholder="例如：季度经营数据分析"
              value={name}
            />
          </label>
          <label className="grid gap-1.5">
            <span className="text-sm font-medium text-slate-700">描述</span>
            <textarea
              className="min-h-24 rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
              maxLength={2000}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="记录本次临时分析任务的范围"
              value={description}
            />
          </label>
          <button
            className="w-fit rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={isSubmitting}
            type="submit"
          >
            {isSubmitting ? "创建中" : "创建任务"}
          </button>
        </form>
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-950">任务列表</h2>
          <span className="text-sm text-slate-500">{tasks.length} 个任务</span>
        </div>

        {isLoading ? <p className="text-sm text-slate-500">加载中</p> : null}

        {!isLoading && tasks.length === 0 ? (
          <div className="rounded-md border border-dashed border-slate-300 bg-white px-4 py-8 text-center text-sm text-slate-500">
            暂无任务
          </div>
        ) : null}

        <div className="grid gap-3">
          {tasks.map((task) => (
            <article key={task.id} className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="flex flex-wrap items-center gap-3">
                    <Link className="text-lg font-semibold text-slate-950 hover:underline" href={`/tasks/${task.id}`}>
                      {task.name}
                    </Link>
                    <span className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">{task.status}</span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{task.description || "无描述"}</p>
                  <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 font-mono text-xs text-slate-500">
                    <span>{task.id}</span>
                    <span>{task.owner_user_id}</span>
                    <span>{task.department_id}</span>
                    <span>{formatDate(task.created_at)}</span>
                  </div>
                </div>
                <button
                  className="rounded-md border border-red-200 px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50"
                  onClick={() => onDelete(task.id)}
                  type="button"
                >
                  删除
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
