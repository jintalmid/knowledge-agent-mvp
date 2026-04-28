"use client";

import Pagination from "@/components/Pagination";
import { ModuleInfo } from "@/lib/api";
import { usePagination } from "@/lib/usePagination";

export default function ModulesClient({ modules }: { modules: ModuleInfo[] }) {
  const modulePagination = usePagination(modules, 10);

  return (
    <>
      <section className="grid gap-3">
        {modulePagination.paginatedItems.map((module) => (
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
      {modules.length > 0 ? (
        <Pagination
          label="个模块"
          onPageChange={modulePagination.setPage}
          onPageSizeChange={modulePagination.setPageSize}
          page={modulePagination.page}
          pageSize={modulePagination.pageSize}
          totalItems={modulePagination.totalItems}
          totalPages={modulePagination.totalPages}
        />
      ) : null}
    </>
  );
}
