import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-6 py-12">
      <p className="text-sm font-medium text-slate-500">Step 0</p>
      <h1 className="mt-3 text-4xl font-semibold text-slate-950">knowledge-agent-mvp</h1>
      <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600">
        阶段 0 项目基座已包含模块注册表、后端健康检查和前端模块列表页。
      </p>
      <Link
        href="/modules"
        className="mt-8 inline-flex w-fit items-center rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
      >
        查看模块列表
      </Link>
      <Link
        href="/tasks"
        className="mt-3 inline-flex w-fit items-center rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-white"
      >
        进入任务空间
      </Link>
    </main>
  );
}
