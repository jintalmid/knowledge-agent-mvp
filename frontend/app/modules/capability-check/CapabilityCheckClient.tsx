"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  CapabilityCheck,
  CapabilityStepStatus,
  getPhase0Requirements,
  getTaskCapabilityCheck,
  getTasks,
  Phase0Requirements,
  Task,
} from "@/lib/api";

const statusStyles: Record<CapabilityStepStatus, string> = {
  passed: "bg-emerald-50 text-emerald-700",
  missing: "bg-amber-50 text-amber-700",
  failed: "bg-red-50 text-red-700",
};

const statusLabels: Record<CapabilityStepStatus, string> = {
  passed: "passed",
  missing: "missing",
  failed: "failed",
};

export default function CapabilityCheckClient() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState("");
  const [requirements, setRequirements] = useState<Phase0Requirements | null>(null);
  const [check, setCheck] = useState<CapabilityCheck | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isChecking, setIsChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const requirementByStep = useMemo(() => {
    return Object.fromEntries((requirements?.requirements ?? []).map((requirement) => [requirement.step, requirement]));
  }, [requirements]);

  async function refreshBase() {
    setIsLoading(true);
    setError(null);
    try {
      const [loadedTasks, loadedRequirements] = await Promise.all([getTasks(), getPhase0Requirements()]);
      setTasks(loadedTasks);
      setRequirements(loadedRequirements);
      setSelectedTaskId((current) => current || loadedTasks[0]?.id || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "能力盘点页面加载失败");
    } finally {
      setIsLoading(false);
    }
  }

  async function runCheck(taskId: string) {
    if (!taskId) {
      setCheck(null);
      return;
    }
    setIsChecking(true);
    setError(null);
    try {
      const loadedCheck = await getTaskCapabilityCheck(taskId);
      setCheck(loadedCheck);
    } catch (err) {
      setError(err instanceof Error ? err.message : "能力检查失败");
    } finally {
      setIsChecking(false);
    }
  }

  useEffect(() => {
    refreshBase();
  }, []);

  useEffect(() => {
    if (selectedTaskId) {
      runCheck(selectedTaskId);
    }
  }, [selectedTaskId]);

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link className="text-sm font-medium text-slate-600 hover:underline" href="/modules">
            返回模块列表
          </Link>
          <p className="mt-4 text-sm font-medium text-slate-500">M12 Capability Check</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">阶段 0 能力盘点</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
            按任务检查阶段 0 最小闭环是否完成，并给出下一步页面入口。
          </p>
        </div>
        <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-white" href="/tasks">
          任务列表
        </Link>
      </header>

      {error ? <div className="mb-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
      {isLoading ? <p className="text-sm text-slate-500">加载中</p> : null}

      <section className="mb-6 rounded-md border border-slate-200 bg-white p-5 shadow-sm">
        <div className="grid gap-4 md:grid-cols-[1fr_auto]">
          <label className="grid gap-1.5">
            <span className="text-sm font-medium text-slate-700">选择任务</span>
            <select
              className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
              onChange={(event) => setSelectedTaskId(event.target.value)}
              value={selectedTaskId}
            >
              <option value="">选择任务</option>
              {tasks.map((task) => (
                <option key={task.id} value={task.id}>
                  {task.name} / {task.id}
                </option>
              ))}
            </select>
          </label>
          <button
            className="h-fit self-end rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={!selectedTaskId || isChecking}
            onClick={() => runCheck(selectedTaskId)}
            type="button"
          >
            {isChecking ? "检查中" : "重新检查"}
          </button>
        </div>
      </section>

      {check ? (
        <section className="grid gap-4">
          <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-mono text-xs text-slate-500">{check.phase}</p>
                <h2 className="mt-1 text-lg font-semibold text-slate-950">{check.task_id}</h2>
              </div>
              <span
                className={
                  check.overall_status === "ready"
                    ? "rounded-md bg-emerald-50 px-2.5 py-1 text-sm font-medium text-emerald-700"
                    : check.overall_status === "failed"
                      ? "rounded-md bg-red-50 px-2.5 py-1 text-sm font-medium text-red-700"
                      : "rounded-md bg-amber-50 px-2.5 py-1 text-sm font-medium text-amber-700"
                }
              >
                {check.overall_status}
              </span>
            </div>
          </div>

          {check.steps.map((step, index) => {
            const requirement = requirementByStep[step.step];
            return (
              <article key={step.step} className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex flex-wrap items-center gap-3">
                      <span className="font-mono text-xs text-slate-500">{String(index + 1).padStart(2, "0")}</span>
                      <h2 className="font-mono text-sm font-semibold text-slate-950">{step.step}</h2>
                      <span className={`rounded-md px-2.5 py-1 text-xs font-medium ${statusStyles[step.status]}`}>
                        {statusLabels[step.status]}
                      </span>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-slate-700">{step.message}</p>
                    {requirement ? (
                      <p className="mt-2 text-xs leading-5 text-slate-500">
                        {requirement.description} / {requirement.module_ids.join(", ")}
                      </p>
                    ) : null}
                  </div>
                  {step.next_page ? (
                    <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50" href={step.next_page}>
                      下一步
                    </Link>
                  ) : null}
                </div>
              </article>
            );
          })}
        </section>
      ) : !isLoading ? (
        <p className="text-sm text-slate-500">请选择一个任务开始检查。</p>
      ) : null}
    </main>
  );
}
