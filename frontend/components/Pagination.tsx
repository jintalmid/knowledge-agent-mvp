"use client";

const pageSizeOptions = [5, 10, 20, 50];

type PaginationProps = {
  label?: string;
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
};

export default function Pagination({
  label = "条目",
  page,
  pageSize,
  totalItems,
  totalPages,
  onPageChange,
  onPageSizeChange,
}: PaginationProps) {
  const start = totalItems === 0 ? 0 : (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, totalItems);
  const canGoPrevious = page > 1;
  const canGoNext = page < totalPages;

  return (
    <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600">
      <div>
        显示 {start}-{end} / {totalItems} {label}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <label className="flex items-center gap-2">
          <span className="text-slate-500">每页</span>
          <select
            className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm outline-none focus:border-slate-500"
            onChange={(event) => onPageSizeChange(Number(event.target.value))}
            value={pageSize}
          >
            {pageSizeOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
        <span className="px-1 text-slate-400">
          {page} / {totalPages}
        </span>
        <button
          className="rounded-md border border-slate-300 px-2 py-1 font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-300"
          disabled={!canGoPrevious}
          onClick={() => onPageChange(1)}
          type="button"
        >
          首页
        </button>
        <button
          className="rounded-md border border-slate-300 px-2 py-1 font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-300"
          disabled={!canGoPrevious}
          onClick={() => onPageChange(page - 1)}
          type="button"
        >
          上一页
        </button>
        <button
          className="rounded-md border border-slate-300 px-2 py-1 font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-300"
          disabled={!canGoNext}
          onClick={() => onPageChange(page + 1)}
          type="button"
        >
          下一页
        </button>
        <button
          className="rounded-md border border-slate-300 px-2 py-1 font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-300"
          disabled={!canGoNext}
          onClick={() => onPageChange(totalPages)}
          type="button"
        >
          末页
        </button>
      </div>
    </div>
  );
}
