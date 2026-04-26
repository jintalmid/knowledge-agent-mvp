"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  analyzeExcelTaskFile,
  ExcelAnalyzeResponse,
  getParsedContent,
  getTask,
  getTaskFiles,
  ParsedContent,
  Task,
  TaskFile,
} from "@/lib/api";
import { copyText } from "@/lib/clipboard";

function sheetNames(parsedContent: ParsedContent | null) {
  const sheets = parsedContent?.excel_profile_json?.sheets;
  if (!Array.isArray(sheets)) {
    return [];
  }
  return sheets
    .map((sheet) => {
      if (sheet && typeof sheet === "object" && "sheet_name" in sheet) {
        return String(sheet.sheet_name);
      }
      return "";
    })
    .filter(Boolean);
}

export default function ExcelClient({ taskId }: { taskId: string }) {
  const [task, setTask] = useState<Task | null>(null);
  const [taskFiles, setTaskFiles] = useState<TaskFile[]>([]);
  const [selectedTaskFileId, setSelectedTaskFileId] = useState("");
  const [parsedContent, setParsedContent] = useState<ParsedContent | null>(null);
  const [sheetName, setSheetName] = useState("");
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<ExcelAnalyzeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const excelFiles = useMemo(
    () => taskFiles.filter((taskFile) => ["xlsx", "xls", "csv"].includes(taskFile.file_ext)),
    [taskFiles],
  );
  const sheets = sheetNames(parsedContent);

  async function refresh() {
    setIsLoading(true);
    setError(null);
    try {
      const [loadedTask, loadedFiles] = await Promise.all([getTask(taskId), getTaskFiles(taskId)]);
      setTask(loadedTask);
      setTaskFiles(loadedFiles);
      const firstExcelFile = loadedFiles.find((taskFile) => ["xlsx", "xls", "csv"].includes(taskFile.file_ext));
      setSelectedTaskFileId((current) => current || firstExcelFile?.id || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Excel 页面加载失败");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, [taskId]);

  useEffect(() => {
    async function loadProfile() {
      if (!selectedTaskFileId) {
        setParsedContent(null);
        setSheetName("");
        return;
      }
      setIsLoadingProfile(true);
      setError(null);
      try {
        const loadedParsedContent = await getParsedContent(selectedTaskFileId);
        setParsedContent(loadedParsedContent);
        const loadedSheets = sheetNames(loadedParsedContent);
        setSheetName(loadedSheets[0] ?? "");
      } catch (err) {
        setParsedContent(null);
        setSheetName("");
        setError(err instanceof Error ? err.message : "Excel profile 加载失败，请先解析文件");
      } finally {
        setIsLoadingProfile(false);
      }
    }
    loadProfile();
  }, [selectedTaskFileId]);

  async function onAnalyze(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTaskFileId) {
      setError("请选择 Excel 文件");
      return;
    }
    if (!question.trim()) {
      setError("请输入分析问题");
      return;
    }

    setIsAnalyzing(true);
    setCopied(false);
    setError(null);
    try {
      const response = await analyzeExcelTaskFile(selectedTaskFileId, {
        question: question.trim(),
        sheet_name: sheetName || null,
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Excel 分析失败");
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function onCopy() {
    if (!result?.answer) {
      return;
    }
    try {
      await copyText(result.answer.answer_text_markdown);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch (err) {
      setError(err instanceof Error ? err.message : "复制失败");
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link className="text-sm font-medium text-slate-600 hover:underline" href={`/tasks/${taskId}`}>
            返回任务详情
          </Link>
          <p className="mt-4 text-sm font-medium text-slate-500">M10 Excel Sandbox Analysis</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">Excel 分析</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">{task ? task.name : taskId}</p>
        </div>
        <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-white" href={`/tasks/${taskId}/results`}>
          历史结果
        </Link>
      </header>

      {error ? <div className="mb-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
      {isLoading ? <p className="text-sm text-slate-500">加载中</p> : null}

      <form className="mb-6 grid gap-4 rounded-md border border-slate-200 bg-white p-5 shadow-sm" onSubmit={onAnalyze}>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="grid gap-1.5">
            <span className="text-sm font-medium text-slate-700">Excel 文件</span>
            <select
              className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
              onChange={(event) => setSelectedTaskFileId(event.target.value)}
              value={selectedTaskFileId}
            >
              <option value="">选择文件</option>
              {excelFiles.map((taskFile) => (
                <option key={taskFile.id} value={taskFile.id}>
                  {taskFile.display_name} / {taskFile.parse_status}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1.5">
            <span className="text-sm font-medium text-slate-700">Sheet</span>
            <select
              className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
              disabled={isLoadingProfile || sheets.length === 0}
              onChange={(event) => setSheetName(event.target.value)}
              value={sheetName}
            >
              <option value="">不指定</option>
              {sheets.map((sheet) => (
                <option key={sheet} value={sheet}>
                  {sheet}
                </option>
              ))}
            </select>
          </label>
        </div>
        <label className="grid gap-1.5">
          <span className="text-sm font-medium text-slate-700">问题</span>
          <textarea
            className="min-h-32 rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
            maxLength={4000}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="例如：统计各部门销售额，并找出最高的前三项"
            value={question}
          />
        </label>
        <button
          className="w-fit rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          disabled={isAnalyzing}
          type="submit"
        >
          {isAnalyzing ? "分析中" : "开始分析"}
        </button>
      </form>

      {result ? (
        <section className="grid gap-4">
          <article className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-slate-950">分析结果</h2>
                <p className="mt-1 font-mono text-xs text-slate-500">
                  execution: {result.run.execution_status} / code: {result.run.code_status} / repairs: {result.run.repair_attempts}
                </p>
              </div>
              <button
                className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-400"
                disabled={!result.answer}
                onClick={onCopy}
                type="button"
              >
                {copied ? "已复制" : "复制 Markdown"}
              </button>
            </div>
            {result.answer ? (
              <div className="whitespace-pre-wrap rounded-md bg-slate-50 p-4 text-sm leading-7 text-slate-800">
                {result.answer.answer_text_markdown}
              </div>
            ) : (
              <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                分析执行失败，未生成 Markdown 答案。请查看 stderr 和 first_error。
              </div>
            )}
          </article>

          <section className="grid gap-4 lg:grid-cols-2">
            <article className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-950">generated_code</h2>
              <pre className="mt-3 max-h-96 overflow-auto rounded-md bg-slate-950 p-4 text-xs leading-6 text-slate-100">
                {result.run.generated_code}
              </pre>
            </article>
            <article className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-950">final_code</h2>
              <pre className="mt-3 max-h-96 overflow-auto rounded-md bg-slate-950 p-4 text-xs leading-6 text-slate-100">
                {result.run.final_code}
              </pre>
            </article>
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <article className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-950">stdout</h2>
              <pre className="mt-3 max-h-72 overflow-auto rounded-md bg-slate-950 p-4 text-xs leading-6 text-slate-100">
                {result.run.stdout || ""}
              </pre>
            </article>
            <article className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-950">stderr</h2>
              <pre className="mt-3 max-h-72 overflow-auto rounded-md bg-slate-950 p-4 text-xs leading-6 text-slate-100">
                {result.run.stderr || result.run.first_error || ""}
              </pre>
            </article>
          </section>

          <article className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-950">result_json</h2>
            <pre className="mt-3 max-h-96 overflow-auto rounded-md bg-slate-950 p-4 text-xs leading-6 text-slate-100">
              {JSON.stringify(result.run.result_json, null, 2)}
            </pre>
          </article>
        </section>
      ) : null}
    </main>
  );
}
