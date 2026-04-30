"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  createModel,
  createModelProvider,
  deleteModel,
  deleteModelProvider,
  getModelProviders,
  getModels,
  ModelConfig,
  ModelProvider,
  testModel,
  updateModel,
  updateModelProvider,
} from "@/lib/api";

function listText(value: string[]) {
  return value.join(", ");
}

const modelTypeOptions = [
  { value: "text", label: "文本生成 / Chat" },
  { value: "vision", label: "视觉语言 / 多模态" },
  { value: "embedding", label: "Embedding 向量" },
  { value: "rerank", label: "Reranker 重排" },
];

const capabilityTagOptions = [
  { value: "text", label: "文本生成" },
  { value: "reasoning", label: "推理" },
  { value: "code", label: "代码生成" },
  { value: "json", label: "JSON 输出" },
  { value: "tool_use", label: "工具调用" },
  { value: "long_context", label: "长上下文" },
  { value: "vision", label: "视觉理解" },
  { value: "document_parse", label: "文档解析" },
  { value: "embedding", label: "向量生成" },
  { value: "rerank", label: "重排序" },
  { value: "ocr", label: "OCR" },
  { value: "excel", label: "表格分析" },
];

const capabilityTagsByModelType: Record<string, string[]> = {
  text: ["text", "reasoning", "code", "json", "tool_use", "long_context", "excel"],
  vision: ["text", "vision", "document_parse", "ocr", "reasoning", "json", "long_context"],
  embedding: ["embedding"],
  rerank: ["rerank"],
};

const defaultTagsByModelType: Record<string, string[]> = {
  text: ["text", "reasoning"],
  vision: ["text", "vision", "document_parse"],
  embedding: ["embedding"],
  rerank: ["rerank"],
};

const providerTypeOptions = [
  { value: "openai_compatible", label: "OpenAI-compatible", note: "当前可执行，适配 OpenAI、Ollama、vLLM、LM Studio 等兼容接口" },
  { value: "openai", label: "OpenAI 官方", note: "预留，可先用 openai_compatible 接入" },
  { value: "azure_openai", label: "Azure OpenAI", note: "预留" },
  { value: "anthropic", label: "Anthropic Claude", note: "预留" },
  { value: "google_gemini", label: "Google Gemini", note: "预留" },
  { value: "ollama", label: "Ollama", note: "预留，可先用 openai_compatible + /v1" },
  { value: "deepseek", label: "DeepSeek", note: "预留，可先用 openai_compatible" },
  { value: "qwen_dashscope", label: "通义千问 / DashScope", note: "预留，可先用兼容接口" },
  { value: "volcengine_ark", label: "火山方舟 Ark", note: "预留，可先用兼容接口" },
  { value: "moonshot", label: "Moonshot / Kimi", note: "预留，可先用兼容接口" },
  { value: "zhipu", label: "智谱 GLM", note: "预留" },
  { value: "baichuan", label: "百川智能", note: "预留" },
  { value: "mistral", label: "Mistral", note: "预留" },
  { value: "cohere", label: "Cohere", note: "预留" },
  { value: "local_runtime", label: "本地 Runtime", note: "预留" },
];

function toggleValue(values: string[], value: string) {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}

function primaryModelType(types: string[]) {
  const value = types[0] || "text";
  return modelTypeOptions.some((option) => option.value === value) ? value : "text";
}

function capabilityOptionsForType(modelType: string) {
  const allowedValues = new Set(capabilityTagsByModelType[modelType] || capabilityTagsByModelType.text);
  return capabilityTagOptions.filter((option) => allowedValues.has(option.value));
}

function normalizedTagsForType(modelType: string, tags: string[]) {
  const allowedValues = new Set(capabilityTagsByModelType[modelType] || capabilityTagsByModelType.text);
  const kept = tags.filter((tag) => allowedValues.has(tag));
  return kept.length > 0 ? kept : defaultTagsByModelType[modelType] || defaultTagsByModelType.text;
}

function SingleChoiceSelector({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: { value: string; label: string }[];
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="grid gap-2">
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => {
          const selected = value === option.value;
          return (
            <button
              className={
                selected
                  ? "rounded-md border border-slate-900 bg-slate-950 px-3 py-1.5 text-sm font-medium text-white"
                  : "rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
              }
              key={option.value}
              onClick={() => onChange(option.value)}
              type="button"
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function ChipSelector({
  label,
  options,
  values,
  onChange,
}: {
  label: string;
  options: { value: string; label: string }[];
  values: string[];
  onChange: (values: string[]) => void;
}) {
  return (
    <div className="grid gap-2">
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => {
          const selected = values.includes(option.value);
          return (
            <button
              className={
                selected
                  ? "rounded-md border border-slate-900 bg-slate-950 px-3 py-1.5 text-sm font-medium text-white"
                  : "rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
              }
              key={option.value}
              onClick={() => onChange(toggleValue(values, option.value))}
              type="button"
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function StatusPill({ active, label }: { active: boolean; label: string }) {
  return (
    <span className={active ? "rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700" : "rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600"}>
      {label}
    </span>
  );
}

function Tags({ values }: { values: string[] }) {
  if (values.length === 0) {
    return <span className="text-xs text-slate-400">无标签</span>;
  }
  return (
    <span className="flex flex-wrap gap-1.5">
      {values.map((value) => (
        <span className="rounded-md bg-slate-100 px-2 py-1 font-mono text-xs text-slate-600" key={value}>
          {value}
        </span>
      ))}
    </span>
  );
}

function ActionButton({ children, onClick, danger = false, disabled = false }: { children: string; onClick: () => void; danger?: boolean; disabled?: boolean }) {
  return (
    <button
      className={
        danger
          ? "rounded-md border border-red-200 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50 disabled:text-slate-400"
          : "rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:text-slate-400"
      }
      disabled={disabled}
      onClick={onClick}
      type="button"
    >
      {children}
    </button>
  );
}

export default function ModelsClient() {
  const [providers, setProviders] = useState<ModelProvider[]>([]);
  const [models, setModels] = useState<ModelConfig[]>([]);
  const [providerForm, setProviderForm] = useState({
    name: "",
    provider_type: "openai_compatible",
    base_url: "",
    api_key_env_name: "",
    api_key: "",
  });
  const [modelForm, setModelForm] = useState({
    provider_id: "",
    display_name: "",
    model_name: "",
    model_types: ["text"],
    capability_tags: ["text", "reasoning"],
    context_window: "",
    output_window: "",
    is_default_text_model: false,
  });
  const [editingModels, setEditingModels] = useState<Record<string, ModelConfig>>({});
  const [creatingModelProviderId, setCreatingModelProviderId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [testingModelId, setTestingModelId] = useState<string | null>(null);

  const defaultTextModel = useMemo(() => models.find((model) => model.is_default_text_model), [models]);
  const modelFormType = primaryModelType(modelForm.model_types);
  const enabledModelCount = models.filter((model) => model.enabled).length;
  const enabledProviderCount = providers.filter((provider) => provider.enabled).length;
  const modelsByProviderId = useMemo(() => {
    return models.reduce<Record<string, ModelConfig[]>>((grouped, model) => {
      const next = grouped;
      if (!next[model.provider_id]) {
        next[model.provider_id] = [];
      }
      next[model.provider_id].push(model);
      return next;
    }, {});
  }, [models]);
  const providerIds = useMemo(() => new Set(providers.map((provider) => provider.id)), [providers]);
  const orphanModels = useMemo(() => models.filter((model) => !providerIds.has(model.provider_id)), [models, providerIds]);

  async function refresh() {
    setError(null);
    try {
      const [loadedProviders, loadedModels] = await Promise.all([getModelProviders(), getModels()]);
      setProviders(loadedProviders);
      setModels(loadedModels);
      setModelForm((current) => ({
        ...current,
        provider_id: current.provider_id || loadedProviders[0]?.id || "",
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "模型配置加载失败");
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function onCreateProvider(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    try {
      await createModelProvider({
        ...providerForm,
        enabled: true,
        api_key: providerForm.api_key || null,
        api_key_env_name: providerForm.api_key_env_name || null,
      });
      setProviderForm({ name: "", provider_type: "openai_compatible", base_url: "", api_key_env_name: "", api_key: "" });
      setMessage("Provider 已创建");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Provider 创建失败");
    }
  }

  async function onCreateModel(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    try {
      await createModel({
        provider_id: modelForm.provider_id,
        display_name: modelForm.display_name,
        model_name: modelForm.model_name,
        model_types_json: modelForm.model_types,
        capability_tags_json: modelForm.capability_tags,
        context_window: modelForm.context_window ? Number(modelForm.context_window) : null,
        output_window: modelForm.output_window ? Number(modelForm.output_window) : null,
        enabled: true,
        is_default_text_model: modelForm.is_default_text_model,
      });
      setModelForm((current) => ({ ...current, display_name: "", model_name: "", context_window: "", output_window: "", is_default_text_model: false }));
      setCreatingModelProviderId(null);
      setMessage("模型已创建");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "模型创建失败");
    }
  }

  async function onTestModel(modelId: string) {
    setTestingModelId(modelId);
    setError(null);
    setMessage(null);
    try {
      const result = await testModel(modelId);
      setMessage(`测试成功：${result.response_preview || result.message}`);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "模型测试失败");
      await refresh();
    } finally {
      setTestingModelId(null);
    }
  }

  async function saveModel(model: ModelConfig) {
    setError(null);
    setMessage(null);
    try {
      await updateModel(model.id, {
        provider_id: model.provider_id,
        display_name: model.display_name,
        model_name: model.model_name,
        model_types_json: model.model_types_json,
        capability_tags_json: model.capability_tags_json,
        context_window: model.context_window,
        output_window: model.output_window,
        enabled: model.enabled,
        is_default_text_model: model.is_default_text_model,
      });
      setEditingModels((current) => {
        const next = { ...current };
        delete next[model.id];
        return next;
      });
      setMessage("模型已更新");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "模型更新失败");
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-7xl px-6 py-10">
      <header className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">M04 Model Registry</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">模型管理</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
            管理 Provider、模型能力标签和 default_text。路由策略在“模型路由”中配置。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link className="rounded-md bg-slate-950 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800" href="/settings/model-routing">
            模型路由
          </Link>
          <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-white" href="/settings/llm">
            兼容配置
          </Link>
        </div>
      </header>

      {error ? <div className="mb-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
      {message ? <div className="mb-5 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{message}</div> : null}

      <section className="mb-6 grid gap-4 md:grid-cols-3">
        <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">default_text</p>
          <p className="mt-2 truncate text-lg font-semibold text-slate-950">{defaultTextModel?.display_name || "未配置"}</p>
          <p className="mt-1 truncate font-mono text-xs text-slate-500">{defaultTextModel?.model_name || "需要至少配置一个默认文本模型"}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">启用模型</p>
          <p className="mt-2 text-lg font-semibold text-slate-950">{enabledModelCount} / {models.length}</p>
          <p className="mt-1 text-xs text-slate-500">用于 scenario 路由选择</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">启用 Provider</p>
          <p className="mt-2 text-lg font-semibold text-slate-950">{enabledProviderCount} / {providers.length}</p>
          <p className="mt-1 text-xs text-slate-500">当前执行只支持 openai_compatible</p>
        </div>
      </section>

      <section className="mb-6 grid gap-3">
        <details className="rounded-md border border-slate-200 bg-white shadow-sm" open={providers.length === 0}>
          <summary className="cursor-pointer px-5 py-4 text-sm font-semibold text-slate-950">新增 Provider</summary>
          <form className="grid gap-3 border-t border-slate-100 px-5 py-4 md:grid-cols-2" onSubmit={onCreateProvider}>
            <label className="grid gap-1 text-sm">
              <span className="text-xs font-medium text-slate-500">名称</span>
              <input className="rounded-md border border-slate-300 px-3 py-2" value={providerForm.name} onChange={(event) => setProviderForm({ ...providerForm, name: event.target.value })} required />
            </label>
            <label className="grid gap-1 text-sm">
              <span className="text-xs font-medium text-slate-500">provider_type</span>
              <select
                className="rounded-md border border-slate-300 px-3 py-2"
                value={providerForm.provider_type}
                onChange={(event) => setProviderForm({ ...providerForm, provider_type: event.target.value })}
                required
              >
                {providerTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <span className="text-xs leading-5 text-slate-500">
                {providerTypeOptions.find((option) => option.value === providerForm.provider_type)?.note}
              </span>
            </label>
            <label className="grid gap-1 text-sm md:col-span-2">
              <span className="text-xs font-medium text-slate-500">base_url</span>
              <input className="rounded-md border border-slate-300 px-3 py-2" value={providerForm.base_url} onChange={(event) => setProviderForm({ ...providerForm, base_url: event.target.value })} required />
            </label>
            <label className="grid gap-1 text-sm md:col-span-2">
              <span className="text-xs font-medium text-slate-500">API Key</span>
              <input className="rounded-md border border-slate-300 px-3 py-2" placeholder="密钥会提交到后端保存；生产环境后续可改为密钥管理服务" type="password" value={providerForm.api_key} onChange={(event) => setProviderForm({ ...providerForm, api_key: event.target.value })} />
            </label>
            <button className="w-fit rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800" type="submit">创建 Provider</button>
          </form>
        </details>
      </section>

      <section className="grid gap-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-950">Provider 与模型</h2>
            <p className="mt-1 text-sm text-slate-500">Provider 是接入通道，模型是挂在该通道下的可调用能力。</p>
          </div>
          <span className="text-sm text-slate-500">{providers.length} 个 Provider / {models.length} 个模型</span>
        </div>
        {providers.length === 0 ? (
          <div className="rounded-md border border-dashed border-slate-300 bg-white px-5 py-8 text-sm text-slate-500">
            还没有 Provider。请先创建一个 OpenAI-compatible Provider，再在它下面添加模型。
          </div>
        ) : null}
        {providers.map((provider) => {
          const providerModels = modelsByProviderId[provider.id] || [];
          return (
            <article className="overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm" key={provider.id}>
              <div className="grid gap-4 border-b border-slate-100 bg-slate-50 px-5 py-4 lg:grid-cols-[1fr_auto]">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="truncate text-base font-semibold text-slate-950">{provider.name}</h3>
                    <span className="rounded-md bg-white px-2 py-1 font-mono text-xs text-slate-600">{provider.provider_type}</span>
                    <StatusPill active={provider.enabled} label={provider.enabled ? "provider enabled" : "provider disabled"} />
                    <span className="rounded-md bg-white px-2 py-1 text-xs font-medium text-slate-600">{providerModels.length} 个模型</span>
                  </div>
                  <p className="mt-2 break-all font-mono text-xs text-slate-500">{provider.base_url}</p>
                  <p className="mt-1 text-xs text-slate-500">API Key：{provider.api_key_configured ? "已配置" : "未配置"}</p>
                </div>
                <div className="flex flex-wrap items-start justify-start gap-2 lg:justify-end">
                  <ActionButton onClick={() => updateModelProvider(provider.id, { enabled: !provider.enabled }).then(refresh)}>{provider.enabled ? "禁用 Provider" : "启用 Provider"}</ActionButton>
                  <ActionButton danger onClick={() => deleteModelProvider(provider.id).then(refresh)}>删除 Provider</ActionButton>
                </div>
              </div>
              <div className="px-5 py-4">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Models under this provider</p>
                  <button
                    className={
                      creatingModelProviderId === provider.id
                        ? "rounded-md bg-slate-950 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800"
                        : "rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
                    }
                    onClick={() => {
                      setCreatingModelProviderId((current) => (current === provider.id ? null : provider.id));
                      setModelForm((current) => ({ ...current, provider_id: provider.id }));
                    }}
                    type="button"
                  >
                    {creatingModelProviderId === provider.id ? "收起新增" : "新增模型"}
                  </button>
                </div>
                {creatingModelProviderId === provider.id ? (
                  <form className="mb-4 grid gap-3 rounded-md border border-slate-200 bg-slate-50 p-4 md:grid-cols-2" onSubmit={onCreateModel}>
                    <div className="md:col-span-2">
                      <p className="text-xs font-medium text-slate-500">所属 Provider</p>
                      <p className="mt-1 break-all text-sm font-medium text-slate-900">{provider.name}</p>
                    </div>
                    <label className="grid gap-1 text-sm">
                      <span className="text-xs font-medium text-slate-500">模型名</span>
                      <input className="rounded-md border border-slate-300 px-3 py-2" value={modelForm.model_name} onChange={(event) => setModelForm({ ...modelForm, provider_id: provider.id, model_name: event.target.value })} required />
                    </label>
                    <label className="grid gap-1 text-sm">
                      <span className="text-xs font-medium text-slate-500">显示名称</span>
                      <input className="rounded-md border border-slate-300 px-3 py-2" value={modelForm.display_name} onChange={(event) => setModelForm({ ...modelForm, provider_id: provider.id, display_name: event.target.value })} required />
                    </label>
                    <label className="grid gap-1 text-sm">
                      <span className="text-xs font-medium text-slate-500">context window</span>
                      <input className="rounded-md border border-slate-300 px-3 py-2" inputMode="numeric" placeholder="例如 128000" value={modelForm.context_window} onChange={(event) => setModelForm({ ...modelForm, provider_id: provider.id, context_window: event.target.value })} />
                    </label>
                    <label className="grid gap-1 text-sm">
                      <span className="text-xs font-medium text-slate-500">output window</span>
                      <input className="rounded-md border border-slate-300 px-3 py-2" inputMode="numeric" placeholder="例如 4096" value={modelForm.output_window} onChange={(event) => setModelForm({ ...modelForm, provider_id: provider.id, output_window: event.target.value })} />
                    </label>
                    <div className="md:col-span-2">
                      <SingleChoiceSelector
                        label="模型类别"
                        onChange={(value) => setModelForm({
                          ...modelForm,
                          provider_id: provider.id,
                          model_types: [value],
                          capability_tags: normalizedTagsForType(value, modelForm.capability_tags),
                          is_default_text_model: value === "text" ? modelForm.is_default_text_model : false,
                        })}
                        options={modelTypeOptions}
                        value={modelFormType}
                      />
                      <p className="mt-2 text-xs leading-5 text-slate-500">
                        模型类别是互斥的主用途。OCR 属于视觉/文档模型的能力标签，不作为独立模型类别。
                      </p>
                    </div>
                    <div className="md:col-span-2">
                      <ChipSelector
                        label="能力标签"
                        onChange={(values) => setModelForm({ ...modelForm, provider_id: provider.id, capability_tags: values })}
                        options={capabilityOptionsForType(modelFormType)}
                        values={modelForm.capability_tags}
                      />
                    </div>
                    <label className="flex items-center gap-2 text-sm text-slate-700">
                      <input checked={modelForm.is_default_text_model && modelFormType === "text"} disabled={modelFormType !== "text"} onChange={(event) => setModelForm({ ...modelForm, provider_id: provider.id, is_default_text_model: event.target.checked })} type="checkbox" />
                      设为 default_text
                    </label>
                    <div className="flex flex-wrap gap-2 md:justify-end">
                      <button className="rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800" type="submit">创建模型</button>
                      <button className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-white" onClick={() => setCreatingModelProviderId(null)} type="button">取消</button>
                    </div>
                  </form>
                ) : null}
                {providerModels.length === 0 ? (
                  <div className="rounded-md border border-dashed border-slate-300 px-4 py-5 text-sm text-slate-500">
                    这个 Provider 下面还没有模型。点击右上方“新增模型”后，会直接把模型创建到当前 Provider 下。
                  </div>
                ) : (
                  <div className="divide-y divide-slate-100 border-y border-slate-100">
                    {providerModels.map((model) => {
                      const edit = editingModels[model.id];
                      const editType = edit ? primaryModelType(edit.model_types_json) : "text";
                      return (
                        <div className="py-4" key={model.id}>
                          <div className="grid gap-4 xl:grid-cols-[1.35fr_1fr_auto]">
                            <div className="min-w-0">
                              <div className="flex flex-wrap items-center gap-2">
                                <h4 className="truncate text-base font-semibold text-slate-950">{model.display_name}</h4>
                                {model.is_default_text_model ? <span className="rounded-md bg-sky-50 px-2 py-1 text-xs font-medium text-sky-700">default_text</span> : null}
                                <StatusPill active={model.enabled} label={model.enabled ? "model enabled" : "model disabled"} />
                              </div>
                              <p className="mt-2 break-all font-mono text-xs text-slate-500">{model.model_name}</p>
                              <p className="mt-1 text-xs text-slate-500">
                                context：{model.context_window || "未设置"} / output：{model.output_window || "未设置"} / test：{model.last_test_status || "未测试"}
                              </p>
                            </div>
                            <div className="grid gap-2">
                              <Tags values={model.capability_tags_json} />
                              <p className="text-xs text-slate-500">types: {listText(model.model_types_json) || "无"}</p>
                            </div>
                            <div className="flex flex-wrap items-start justify-start gap-2 xl:justify-end">
                              <ActionButton disabled={testingModelId === model.id} onClick={() => onTestModel(model.id)}>{testingModelId === model.id ? "测试中" : "测试"}</ActionButton>
                              <ActionButton onClick={() => updateModel(model.id, { enabled: !model.enabled }).then(refresh)}>{model.enabled ? "禁用" : "启用"}</ActionButton>
                              <ActionButton onClick={() => updateModel(model.id, { is_default_text_model: true }).then(refresh)}>设默认</ActionButton>
                              <ActionButton onClick={() => setEditingModels((current) => ({ ...current, [model.id]: model }))}>编辑</ActionButton>
                              <ActionButton danger onClick={() => deleteModel(model.id).then(refresh)}>删除</ActionButton>
                            </div>
                          </div>

                          {edit ? (
                            <div className="mt-4 grid gap-3 rounded-md border border-slate-100 bg-slate-50 p-3 md:grid-cols-2">
                              <label className="grid gap-1 text-sm">
                                <span className="text-xs font-medium text-slate-500">显示名称</span>
                                <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={edit.display_name} onChange={(event) => setEditingModels((current) => ({ ...current, [model.id]: { ...edit, display_name: event.target.value } }))} />
                              </label>
                              <label className="grid gap-1 text-sm">
                                <span className="text-xs font-medium text-slate-500">模型名</span>
                                <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={edit.model_name} onChange={(event) => setEditingModels((current) => ({ ...current, [model.id]: { ...edit, model_name: event.target.value } }))} />
                              </label>
                              <label className="grid gap-1 text-sm">
                                <span className="text-xs font-medium text-slate-500">context window</span>
                                <input
                                  className="rounded-md border border-slate-300 px-3 py-2 text-sm"
                                  inputMode="numeric"
                                  value={edit.context_window ?? ""}
                                  onChange={(event) => setEditingModels((current) => ({ ...current, [model.id]: { ...edit, context_window: event.target.value ? Number(event.target.value) : null } }))}
                                />
                              </label>
                              <label className="grid gap-1 text-sm">
                                <span className="text-xs font-medium text-slate-500">output window</span>
                                <input
                                  className="rounded-md border border-slate-300 px-3 py-2 text-sm"
                                  inputMode="numeric"
                                  value={edit.output_window ?? ""}
                                  onChange={(event) => setEditingModels((current) => ({ ...current, [model.id]: { ...edit, output_window: event.target.value ? Number(event.target.value) : null } }))}
                                />
                              </label>
                              <div className="md:col-span-2">
                                <SingleChoiceSelector
                                  label="模型类别"
                                  onChange={(value) => setEditingModels((current) => ({
                                    ...current,
                                    [model.id]: {
                                      ...edit,
                                      model_types_json: [value],
                                      capability_tags_json: normalizedTagsForType(value, edit.capability_tags_json),
                                      is_default_text_model: value === "text" ? edit.is_default_text_model : false,
                                    },
                                  }))}
                                  options={modelTypeOptions}
                                  value={editType}
                                />
                                <p className="mt-2 text-xs leading-5 text-slate-500">
                                  模型类别是互斥的主用途。OCR 属于视觉/文档模型的能力标签，不作为独立模型类别。
                                </p>
                              </div>
                              <div className="md:col-span-2">
                                <ChipSelector
                                  label="能力标签"
                                  onChange={(values) => setEditingModels((current) => ({ ...current, [model.id]: { ...edit, capability_tags_json: values } }))}
                                  options={capabilityOptionsForType(editType)}
                                  values={edit.capability_tags_json}
                                />
                              </div>
                              <label className="flex items-center gap-2 text-sm text-slate-700">
                                <input checked={edit.is_default_text_model && editType === "text"} disabled={editType !== "text"} onChange={(event) => setEditingModels((current) => ({ ...current, [model.id]: { ...edit, is_default_text_model: event.target.checked } }))} type="checkbox" />
                                设为 default_text
                              </label>
                              <label className="flex items-center gap-2 text-sm text-slate-700">
                                <input checked={edit.enabled} onChange={(event) => setEditingModels((current) => ({ ...current, [model.id]: { ...edit, enabled: event.target.checked } }))} type="checkbox" />
                                启用模型
                              </label>
                              <div className="flex gap-2 md:col-span-2">
                                <button className="rounded-md bg-slate-950 px-3 py-2 text-sm font-medium text-white" onClick={() => saveModel(edit)} type="button">保存</button>
                                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm" onClick={() => setEditingModels((current) => { const next = { ...current }; delete next[model.id]; return next; })} type="button">取消</button>
                              </div>
                            </div>
                          ) : null}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </article>
          );
        })}

        {orphanModels.length > 0 ? (
          <div className="rounded-md border border-amber-200 bg-amber-50 px-5 py-4">
            <h3 className="text-sm font-semibold text-amber-900">未匹配到 Provider 的模型</h3>
            <div className="mt-3 grid gap-2">
              {orphanModels.map((model) => (
                <div className="rounded-md bg-white px-3 py-2 text-sm text-amber-900" key={model.id}>
                  {model.display_name} / {model.model_name} / provider_id: {model.provider_id}
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </section>
    </main>
  );
}
