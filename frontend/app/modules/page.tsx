import Link from "next/link";
import { getModules } from "@/lib/api";

export default async function ModulesPage() {
  const modules = await getModules();

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">Module Registry</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">模块列表</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
            当前页面展示阶段 0 的模块注册信息和能力检查入口。
          </p>
        </div>
        <Link
          className="rounded-md bg-slate-950 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800"
          href="/modules/capability-check"
        >
          阶段 0 能力盘点
        </Link>
      </header>

      <section className="grid gap-3">
        {modules.map((module) => (
          <article key={module.id} className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-3">
                  <span className="font-mono text-sm font-semibold text-slate-500">{module.id}</span>
                  <h2 className="text-lg font-semibold text-slate-950">{module.name}</h2>
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-600">{module.description}</p>
                <p className="mt-3 font-mono text-xs text-slate-500">{module.doc}</p>
              </div>
              <span
                className={
                  module.enabled
                    ? "rounded-md bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700"
                    : "rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600"
                }
              >
                {module.status}
              </span>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
