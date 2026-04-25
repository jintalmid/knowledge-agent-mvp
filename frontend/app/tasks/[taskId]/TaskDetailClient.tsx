"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { deleteTask, getTask, Task, TaskStatus, updateTask } from "@/lib/api";

const nextModuleEntries = [
  { label: "M03 物理文件资产与去重", implemented: true },
  { label: "M04 任务文件引用", implemented: true },
  { label: "M05 文件解析", implemented: false },
  { label: "M06 LLM 摘要与标签", implemented: false },
  { label: "M07 Chunk / RAG 配置预留", implemented: false },
  { label: "M08 临时检索与文件筛选", implemented: false },
  { label: "M09 文本问答与临时处理", implemented: false },
  { label: "M10 Excel 分析与受限代码沙箱", implemented: false },
  { label: "M11 结果与来源展示", implemented: false },
  { label: "M13 LLM 调用日志与 Debug", implemented: false },
];

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function TaskDetailClient({ taskId }: { taskId: string }) {
  const router = useRouter();
  const [task, setTask] = useState<Task | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<TaskStatus>("draft");
  const [knowledgeBaseId, setKnowledgeBaseId] = useState("");
  const [templateId, setTemplateId] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refreshTask() {
    setIsLoading(true);
    setError(null);
    try {
      const loadedTask = await getTask(taskId);
      setTask(loadedTask);
      setName(loadedTask.name);
      setDescription(loadedTask.description);
      setStatus(loadedTask.status);
      setKnowledgeBaseId(loadedTask.knowledge_base_id ?? "");
      setTemplateId(loadedTask.template_id ?? "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "任务加载失败");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    refreshTask();
  }, [taskId]);

  async function onSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!name.trim()) {
      setError("任务名称不能为空");
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      const savedTask = await updateTask(taskId, {
        name: name.trim(),
        description: description.trim(),
        status,
        knowledge_base_id: knowledgeBaseId.trim() || null,
        template_id: templateId.trim() || null,
      });
      setTask(savedTask);
    } catch (err) {
      setError(err instanceof Error ? err.message : "任务保存失败");
    } finally {
      setIsSaving(false);
    }
  }

  async function onDelete() {
    setError(null);
    try {
      await deleteTask(taskId);
      router.push("/tasks");
    } catch (err) {
      setError(err instanceof Error ? err.message : "任务删除失败");
    }
  }

  if (isLoading) {
    return (
      <main className="mx-auto min-h-screen max-w-5xl px-6 py-10">
        <p className="text-sm text-slate-500">加载中</p>
      </main>
    );
  }

  if (!task) {
    return (
      <main className="mx-auto min-h-screen max-w-5xl px-6 py-10">
        <Link className="text-sm font-medium text-slate-600 hover:underline" href="/tasks">
          返回任务列表
        </Link>
        <div className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error ?? "任务不存在"}
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link className="text-sm font-medium text-slate-600 hover:underline" href="/tasks">
            返回任务列表
          </Link>
          <h1 className="mt-3 text-3xl font-semibold text-slate-950">{task.name}</h1>
          <p className="mt-3 font-mono text-xs text-slate-500">{task.id}</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link
            className="rounded-md bg-slate-950 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800"
            href={`/tasks/${taskId}/files`}
          >
            管理文件
          </Link>
          <button
            className="rounded-md border border-red-200 px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50"
            onClick={onDelete}
            type="button"
          >
            删除任务
          </button>
        </div>
      </header>

      {error ? (
        <div className="mb-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      ) : null}

      <section className="mb-8 grid gap-4 rounded-md border border-slate-200 bg-white p-5 shadow-sm md:grid-cols-3">
        <div>
          <p className="text-xs font-medium text-slate-500">默认用户</p>
          <p className="mt-1 font-mono text-sm text-slate-900">{task.owner_user_id}</p>
        </div>
        <div>
          <p className="text-xs font-medium text-slate-500">默认部门</p>
          <p className="mt-1 font-mono text-sm text-slate-900">{task.department_id}</p>
        </div>
        <div>
          <p className="text-xs font-medium text-slate-500">安全等级</p>
          <p className="mt-1 font-mono text-sm text-slate-900">{task.security_level}</p>
        </div>
        <div>
          <p className="text-xs font-medium text-slate-500">迭代次数</p>
          <p className="mt-1 font-mono text-sm text-slate-900">{task.iteration_count}</p>
        </div>
        <div>
          <p className="text-xs font-medium text-slate-500">创建时间</p>
          <p className="mt-1 text-sm text-slate-900">{formatDate(task.created_at)}</p>
        </div>
        <div>
          <p className="text-xs font-medium text-slate-500">更新时间</p>
          <p className="mt-1 text-sm text-slate-900">{formatDate(task.updated_at)}</p>
        </div>
      </section>

      <section className="mb-8 rounded-md border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-950">任务信息</h2>
        <form className="mt-4 grid gap-4" onSubmit={onSave}>
          <label className="grid gap-1.5">
            <span className="text-sm font-medium text-slate-700">名称</span>
            <input
              className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
              maxLength={120}
              onChange={(event) => setName(event.target.value)}
              value={name}
            />
          </label>
          <label className="grid gap-1.5">
            <span className="text-sm font-medium text-slate-700">描述</span>
            <textarea
              className="min-h-24 rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
              maxLength={2000}
              onChange={(event) => setDescription(event.target.value)}
              value={description}
            />
          </label>
          <div className="grid gap-4 md:grid-cols-3">
            <label className="grid gap-1.5">
              <span className="text-sm font-medium text-slate-700">状态</span>
              <select
                className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
                onChange={(event) => setStatus(event.target.value as TaskStatus)}
                value={status}
              >
                <option value="draft">draft</option>
                <option value="active">active</option>
                <option value="archived">archived</option>
              </select>
            </label>
            <label className="grid gap-1.5">
              <span className="text-sm font-medium text-slate-700">知识库 ID 预留</span>
              <input
                className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
                maxLength={120}
                onChange={(event) => setKnowledgeBaseId(event.target.value)}
                value={knowledgeBaseId}
              />
            </label>
            <label className="grid gap-1.5">
              <span className="text-sm font-medium text-slate-700">模板 ID 预留</span>
              <input
                className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
                maxLength={120}
                onChange={(event) => setTemplateId(event.target.value)}
                value={templateId}
              />
            </label>
          </div>
          <button
            className="w-fit rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={isSaving}
            type="submit"
          >
            {isSaving ? "保存中" : "保存任务"}
          </button>
        </form>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-slate-950">后续模块入口</h2>
        <div className="grid gap-3 md:grid-cols-2">
          {nextModuleEntries.map((entry) => (
            <div key={entry.label} className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between gap-3">
                {entry.implemented ? (
                  <Link className="text-sm font-medium text-slate-900 hover:underline" href={`/tasks/${taskId}/files`}>
                    {entry.label}
                  </Link>
                ) : (
                  <span className="text-sm font-medium text-slate-900">{entry.label}</span>
                )}
                <span
                  className={
                    entry.implemented
                      ? "rounded-md bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700"
                      : "rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600"
                  }
                >
                  {entry.implemented ? "已实现" : "未实现"}
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
