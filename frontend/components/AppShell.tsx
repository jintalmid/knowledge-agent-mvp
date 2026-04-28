"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";
import { getTask, Task } from "@/lib/api";

type NavItem = {
  href: string;
  label: string;
  hint: string;
  exact?: boolean;
  matchPrefixes?: string[];
};

const globalNav: NavItem[] = [
  { href: "/", label: "首页", hint: "Overview" },
  { href: "/tasks", label: "任务", hint: "Workspaces" },
  { href: "/modules", label: "模块", hint: "M00-M13" },
  { href: "/settings/models", label: "模型", hint: "Routing", matchPrefixes: ["/settings/model-routing", "/settings/llm"] },
  { href: "/debug/llm-logs", label: "日志", hint: "Debug" },
];

const modelNav: NavItem[] = [
  { href: "/settings/models", label: "Provider / 模型", hint: "Registry", exact: true },
  { href: "/settings/model-routing", label: "模型路由", hint: "Scenario", exact: true },
  { href: "/settings/llm", label: "兼容配置", hint: "Legacy", exact: true },
  { href: "/debug/llm-logs", label: "调用日志", hint: "Debug", exact: true },
];

function taskNav(taskId: string): NavItem[] {
  return [
    { href: `/tasks/${taskId}`, label: "总览", hint: "Task", exact: true },
    { href: `/tasks/${taskId}/files`, label: "文件", hint: "Upload" },
    { href: `/tasks/${taskId}/summaries`, label: "摘要", hint: "Summary" },
    { href: `/tasks/${taskId}/agent`, label: "Agent", hint: "Run" },
    { href: `/tasks/${taskId}/results`, label: "结果", hint: "Answers" },
    { href: `/tasks/${taskId}/parsing`, label: "解析", hint: "Debug" },
    { href: `/tasks/${taskId}/excel`, label: "Excel", hint: "Tool" },
  ];
}

function taskIdFromPath(pathname: string) {
  const match = pathname.match(/^\/tasks\/([^/]+)/);
  return match?.[1] ?? null;
}

function isActive(pathname: string, href: string) {
  if (href === "/") {
    return pathname === "/";
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

function isActiveItem(pathname: string, item: NavItem) {
  if (item.exact) {
    return pathname === item.href;
  }
  return isActive(pathname, item.href) || Boolean(item.matchPrefixes?.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`)));
}

function isModelScope(pathname: string) {
  return modelNav.some((item) => isActiveItem(pathname, item));
}

function NavLink({ item, pathname }: { item: NavItem; pathname: string }) {
  const active = isActiveItem(pathname, item);
  return (
    <Link
      className={
        active
          ? "block rounded-md border border-slate-900 bg-slate-950 px-3 py-2 text-white shadow-sm"
          : "block rounded-md border border-transparent px-3 py-2 text-slate-600 hover:border-slate-200 hover:bg-slate-50 hover:text-slate-950"
      }
      href={item.href}
    >
      <span className="block text-sm font-medium">{item.label}</span>
      <span className={active ? "block text-xs text-slate-300" : "block text-xs text-slate-400"}>{item.hint}</span>
    </Link>
  );
}

export default function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const taskId = taskIdFromPath(pathname);
  const [currentTask, setCurrentTask] = useState<Task | null>(null);
  const [taskLoadFailed, setTaskLoadFailed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const scopedNav = taskId ? taskNav(taskId) : [];
  const modelScopedNav = !taskId && isModelScope(pathname) ? modelNav : [];
  const mobileScopedNav = scopedNav.length > 0 ? scopedNav : modelScopedNav;
  const mobileScopedTitle = scopedNav.length > 0 ? "当前任务" : modelScopedNav.length > 0 ? "模型设置" : null;
  const mobileScopedSummary = scopedNav.length > 0
    ? currentTask?.name ?? (taskLoadFailed ? "任务加载失败" : "加载任务中...")
    : modelScopedNav.length > 0
      ? "Provider、模型与场景路由"
      : null;

  useEffect(() => {
    let cancelled = false;

    if (!taskId) {
      setCurrentTask(null);
      setTaskLoadFailed(false);
      return;
    }

    setTaskLoadFailed(false);
    getTask(taskId)
      .then((task) => {
        if (!cancelled) {
          setCurrentTask(task);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setCurrentTask(null);
          setTaskLoadFailed(true);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [taskId]);

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto flex min-h-screen w-full max-w-[1500px]">
        <aside className="hidden w-72 shrink-0 border-r border-slate-200 bg-white px-4 py-5 shadow-[8px_0_30px_rgba(15,23,42,0.035)] lg:block">
          <Link href="/" className="block rounded-md border border-slate-200 bg-slate-50 px-3 py-3 hover:bg-white">
            <p className="text-sm font-semibold text-slate-950">knowledge-agent-mvp</p>
            <p className="mt-1 text-xs text-slate-500">Agent Runner Phase 0</p>
            <span className="mt-3 inline-flex rounded-md bg-white px-2 py-1 text-xs font-medium text-slate-500 ring-1 ring-slate-200">
              v0.3 MVP
            </span>
          </Link>

          <nav className="mt-6 grid gap-1">
            {globalNav.map((item) => (
              <NavLink item={item} key={item.href} pathname={pathname} />
            ))}
          </nav>

          {taskId ? (
            <section className="mt-7 border-t border-slate-200 pt-5">
              <p className="px-3 text-xs font-medium uppercase text-slate-400">当前任务</p>
              <p className="mt-2 rounded-md bg-slate-50 px-3 py-2 text-sm font-medium leading-5 text-slate-700" title={taskId}>
                {currentTask?.name ?? (taskLoadFailed ? "任务加载失败" : "加载任务中...")}
              </p>
              <nav className="mt-3 grid gap-1">
                {scopedNav.map((item) => (
                  <NavLink item={item} key={item.href} pathname={pathname} />
                ))}
              </nav>
            </section>
          ) : null}

          {modelScopedNav.length > 0 ? (
            <section className="mt-7 border-t border-slate-200 pt-5">
              <p className="px-3 text-xs font-medium uppercase text-slate-400">模型设置</p>
              <p className="mt-2 rounded-md bg-slate-50 px-3 py-2 text-sm font-medium leading-5 text-slate-700">
                Provider、模型与场景路由
              </p>
              <nav className="mt-3 grid gap-1">
                {modelScopedNav.map((item) => (
                  <NavLink item={item} key={item.href} pathname={pathname} />
                ))}
              </nav>
            </section>
          ) : null}
        </aside>

        <div className="min-w-0 flex-1">
          <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 px-4 py-3 shadow-sm backdrop-blur lg:hidden">
            <div className="flex items-center justify-between gap-3">
              <Link className="text-sm font-semibold text-slate-950" href="/">
                knowledge-agent-mvp
              </Link>
              <button
                aria-expanded={mobileMenuOpen}
                className="rounded-md bg-slate-950 px-3 py-1.5 text-xs font-medium text-white"
                onClick={() => setMobileMenuOpen((open) => !open)}
                type="button"
              >
                {mobileMenuOpen ? "收起目录" : "打开目录"}
              </button>
            </div>
            {mobileMenuOpen ? (
              <div className="mt-3 rounded-md border border-slate-200 bg-white p-3 shadow-lg">
                <section>
                  <p className="px-2 text-xs font-medium uppercase text-slate-400">主导航</p>
                  <nav className="mt-2 grid gap-1">
                    {globalNav.map((item) => (
                      <NavLink item={item} key={item.href} pathname={pathname} />
                    ))}
                  </nav>
                </section>
                {mobileScopedTitle ? (
                  <section className="mt-4 border-t border-slate-100 pt-4">
                    <p className="px-2 text-xs font-medium uppercase text-slate-400">{mobileScopedTitle}</p>
                    <p className="mt-2 rounded-md bg-slate-50 px-3 py-2 text-sm font-medium leading-5 text-slate-700">
                      {mobileScopedSummary}
                    </p>
                    <nav className="mt-2 grid gap-1">
                      {mobileScopedNav.map((item) => (
                        <NavLink item={item} key={item.href} pathname={pathname} />
                      ))}
                    </nav>
                  </section>
                ) : null}
              </div>
            ) : null}
          </header>

          <div className="mx-auto w-full max-w-7xl px-4 lg:px-8">{children}</div>
        </div>
      </div>
    </div>
  );
}
