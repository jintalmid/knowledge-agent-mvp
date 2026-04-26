import Link from "next/link";

const entryCards = [
  {
    href: "/tasks",
    title: "任务空间",
    description: "创建任务、上传文件、启动 Agent Run。",
    action: "进入任务",
  },
  {
    href: "/modules",
    title: "模块地图",
    description: "查看 M00-M13 的实现状态和说明文档。",
    action: "查看模块",
  },
  {
    href: "/settings/llm",
    title: "LLM 配置",
    description: "检查模型配置并测试 OpenAI-compatible 服务。",
    action: "检查配置",
  },
  {
    href: "/debug/llm-logs",
    title: "Debug 日志",
    description: "追踪 plan、tool、reflection 和 final answer 的 LLM 调用。",
    action: "打开日志",
  },
];

export default function HomePage() {
  return (
    <main className="mx-auto min-h-screen max-w-6xl px-0 py-8 lg:py-10">
      <section className="overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 bg-slate-50 px-6 py-4">
          <p className="text-sm font-medium text-slate-500">v0.3 AutoGPT / ReAct Phase 0</p>
        </div>
        <div className="p-6">
        <h1 className="mt-2 text-3xl font-semibold text-slate-950">knowledge-agent-mvp 工作台</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
          当前主流程是创建任务空间、上传文件自动解析、启动 Agent Run，并查看每轮工具调用、观察、反思和最终答案。
        </p>
        <div className="mt-5 flex flex-wrap gap-2">
          <span className="rounded-md bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">文件自动解析</span>
          <span className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">ReAct Loop</span>
          <span className="rounded-md bg-sky-50 px-2.5 py-1 text-xs font-medium text-sky-700">Excel Sandbox</span>
        </div>
        </div>
      </section>

      <section className="mt-5 grid gap-4 md:grid-cols-2">
        {entryCards.map((entry) => (
          <Link
            className="group rounded-md border border-slate-200 bg-white p-5 shadow-sm hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md"
            href={entry.href}
            key={entry.href}
          >
            <h2 className="text-lg font-semibold text-slate-950">{entry.title}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">{entry.description}</p>
            <span className="mt-4 inline-block text-sm font-medium text-slate-900 group-hover:underline">{entry.action}</span>
          </Link>
        ))}
      </section>
    </main>
  );
}
