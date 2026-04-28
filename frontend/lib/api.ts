export type ModuleInfo = {
  id: string;
  name: string;
  status: string;
  description: string;
  doc: string;
  enabled: boolean;
};

export type TaskStatus = "draft" | "active" | "archived";

export type Task = {
  id: string;
  name: string;
  description: string;
  status: TaskStatus;
  owner_user_id: string;
  department_id: string;
  security_level: string;
  knowledge_base_id: string | null;
  template_id: string | null;
  iteration_count: number;
  created_at: string;
  updated_at: string;
};

export type TaskCreatePayload = {
  name: string;
  description: string;
  knowledge_base_id?: string | null;
  template_id?: string | null;
};

export type TaskUpdatePayload = Partial<{
  name: string;
  description: string;
  status: TaskStatus;
  knowledge_base_id: string | null;
  template_id: string | null;
  iteration_count: number;
}>;

export type TaskFile = {
  id: string;
  task_id: string;
  physical_file_id: string;
  display_name: string;
  file_role: string;
  parse_status: string;
  parse_error: string | null;
  summary_status: string;
  embedding_status: string;
  owner_user_id: string;
  department_id: string;
  security_level: string;
  created_at: string;
  updated_at: string;
  file_ext: string;
  mime_type: string;
  file_size: number;
  ref_count: number;
  reused_existing_file: boolean;
};

export type PhysicalFile = {
  id: string;
  content_hash: string;
  original_filename: string;
  file_ext: string;
  mime_type: string;
  file_size: number;
  storage_path: string;
  ref_count: number;
  created_at: string;
  updated_at: string;
};

export type ParsedContent = {
  id: string;
  task_file_id: string;
  physical_file_id: string;
  content_type: "text" | "excel" | string;
  text_content: string | null;
  excel_profile_json: Record<string, unknown> | null;
  parse_quality: string;
  created_at: string;
  updated_at: string;
};

export type FileSummary = {
  id: string;
  task_file_id: string;
  physical_file_id: string;
  summary_text: string;
  keywords_json: string[];
  tags_json: string[];
  category: string;
  summary_method: string;
  llm_provider: string;
  llm_model: string;
  knowledge_item_id: string | null;
  table_understanding: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type LlmSettings = {
  provider_type: string | null;
  base_url_configured: boolean;
  api_key_configured: boolean;
  model: string | null;
  ready: boolean;
};

export type LlmTestResult = {
  status: string;
  response_preview: string;
  log_id: string;
};

export type LlmCallLog = {
  id: string;
  task_id: string | null;
  task_name: string | null;
  owner_user_id: string | null;
  department_id: string | null;
  security_level: string | null;
  agent_run_id: string | null;
  iteration_id: string | null;
  module_name: string;
  provider_type: string;
  model_name: string;
  prompt_preview: string;
  response_preview: string | null;
  status: string;
  error_message: string | null;
  latency_ms: number;
  created_at: string;
};

export type RetrievalMode = "summary_only" | "chunk_text" | "embedding" | "hybrid";

export type DocumentChunk = {
  id: string;
  task_file_id: string;
  physical_file_id: string;
  chunk_index: number;
  content: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type RetrievalSettings = {
  retrieval_mode: RetrievalMode;
  chunk_size: number;
  chunk_overlap: number;
  top_k: number;
  embedding_provider: string | null;
  embedding_model: string | null;
  vector_store: string | null;
  updated_at: string;
};

export type RetrievalSettingsUpdate = Partial<{
  retrieval_mode: RetrievalMode;
  chunk_size: number;
  chunk_overlap: number;
  top_k: number;
  embedding_provider: string | null;
  embedding_model: string | null;
  vector_store: string | null;
}>;

export type ChunkMatch = {
  chunk_id: string;
  chunk_index: number;
  score: number;
  preview: string;
};

export type RetrievalCandidate = {
  task_file_id: string;
  physical_file_id: string;
  display_name: string;
  score: number;
  matched_fields: string[];
  reason: string;
  chunk_matches: ChunkMatch[];
};

export type RetrieveResponse = {
  retrieval_mode: RetrievalMode;
  status: string;
  message: string;
  results: RetrievalCandidate[];
};

export type SourceRef = {
  task_file_id: string;
  physical_file_id: string;
  display_name: string;
  score: number;
  matched_fields: string[];
  reason: string;
  content_type: string;
  chunk_refs: Record<string, unknown>[];
};

export type Answer = {
  id: string;
  task_id: string;
  agent_run_id: string | null;
  question_id: string;
  question_text: string;
  question_type: string;
  answer_text_markdown: string;
  selected_task_file_ids_json: string[];
  source_refs_json: SourceRef[];
  iteration_count: number;
  llm_provider: string;
  llm_model: string;
  created_at: string;
};

export type ExcelAnalysisRun = {
  id: string;
  task_id: string;
  agent_run_id: string | null;
  iteration_id: string | null;
  task_file_id: string;
  question_id: string;
  generated_code: string;
  final_code: string;
  code_status: string;
  execution_status: string;
  result_json: Record<string, unknown> | unknown[] | null;
  stdout: string | null;
  stderr: string | null;
  repair_attempts: number;
  first_error: string | null;
  created_at: string;
  updated_at: string;
};

export type ExcelAnalyzeResponse = {
  run: ExcelAnalysisRun;
  answer: Answer | null;
};

export type CapabilityStepStatus = "passed" | "missing" | "failed";

export type CapabilityStep = {
  step: string;
  status: CapabilityStepStatus;
  message: string;
  next_page: string | null;
};

export type CapabilityCheck = {
  task_id: string;
  phase: string;
  steps: CapabilityStep[];
  overall_status: "ready" | "incomplete" | "failed";
};

export type AgentRunStartResponse = {
  agent_run_id: string;
  answer_id: string | null;
  status: string;
  iteration_count: number;
};

export type AgentObservation = {
  id: string;
  agent_run_id: string;
  agent_iteration_id: string;
  tool_name: string;
  observation_type: string;
  content_text: string | null;
  content_json: Record<string, unknown> | null;
  status: string;
  error_message: string | null;
  created_at: string;
};

export type AgentIteration = {
  id: string;
  agent_run_id: string;
  iteration_index: number;
  plan_text: Record<string, unknown> | null;
  tool_name: string | null;
  tool_input_json: Record<string, unknown> | null;
  tool_result_json: Record<string, unknown> | null;
  reflection_text: Record<string, unknown> | null;
  decision: string;
  llm_call_log_id: string | null;
  status: string;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
  observations: AgentObservation[];
};

export type AgentRun = {
  id: string;
  task_id: string | null;
  goal: string;
  status: string;
  max_iterations: number;
  current_iteration: number;
  final_answer_markdown: string | null;
  stop_reason: string | null;
  owner_user_id: string;
  department_id: string;
  security_level: string;
  created_at: string;
  updated_at: string;
  iterations: AgentIteration[];
};

export type Phase0Requirement = {
  step: string;
  description: string;
  module_ids: string[];
  recommended_page: string;
};

export type Phase0Requirements = {
  phase: string;
  requirements: Phase0Requirement[];
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function getApiBaseUrl() {
  return API_BASE_URL;
}

export async function getModules(): Promise<ModuleInfo[]> {
  const response = await fetch(`${API_BASE_URL}/api/modules`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to load module registry");
  }

  return response.json();
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }

  return response.json();
}

export async function getTasks(): Promise<Task[]> {
  return requestJson<Task[]>("/api/tasks");
}

export async function getTask(taskId: string): Promise<Task> {
  return requestJson<Task>(`/api/tasks/${taskId}`);
}

export async function createTask(payload: TaskCreatePayload): Promise<Task> {
  return requestJson<Task>("/api/tasks", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateTask(taskId: string, payload: TaskUpdatePayload): Promise<Task> {
  return requestJson<Task>(`/api/tasks/${taskId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteTask(taskId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}`, {
    method: "DELETE",
    cache: "no-store",
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }
}

export async function getTaskFiles(taskId: string): Promise<TaskFile[]> {
  return requestJson<TaskFile[]>(`/api/tasks/${taskId}/files`);
}

export async function uploadTaskFile(taskId: string, file: File): Promise<TaskFile> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}/files`, {
    method: "POST",
    body: formData,
    cache: "no-store",
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }

  return response.json();
}

export async function getTaskFile(taskFileId: string): Promise<TaskFile> {
  return requestJson<TaskFile>(`/api/task-files/${taskFileId}`);
}

export async function deleteTaskFile(taskFileId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/task-files/${taskFileId}`, {
    method: "DELETE",
    cache: "no-store",
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }
}

export async function getPhysicalFile(physicalFileId: string): Promise<PhysicalFile> {
  return requestJson<PhysicalFile>(`/api/physical-files/${physicalFileId}`);
}

export async function parseTaskFile(taskFileId: string): Promise<ParsedContent> {
  return requestJson<ParsedContent>(`/api/task-files/${taskFileId}/parse`, {
    method: "POST",
  });
}

export async function parseAllTaskFiles(taskId: string): Promise<ParsedContent[]> {
  return requestJson<ParsedContent[]>(`/api/tasks/${taskId}/parse-all`, {
    method: "POST",
  });
}

export async function getParsedContent(taskFileId: string): Promise<ParsedContent> {
  return requestJson<ParsedContent>(`/api/task-files/${taskFileId}/parsed-content`);
}

export async function summarizeTaskFile(taskFileId: string): Promise<FileSummary> {
  return requestJson<FileSummary>(`/api/task-files/${taskFileId}/summarize`, {
    method: "POST",
  });
}

export async function summarizeAllTaskFiles(taskId: string): Promise<FileSummary[]> {
  return requestJson<FileSummary[]>(`/api/tasks/${taskId}/summarize-all`, {
    method: "POST",
  });
}

export async function getTaskSummaries(taskId: string): Promise<FileSummary[]> {
  return requestJson<FileSummary[]>(`/api/tasks/${taskId}/summaries`);
}

export async function getTaskFileSummary(taskFileId: string): Promise<FileSummary> {
  return requestJson<FileSummary>(`/api/task-files/${taskFileId}/summary`);
}

export async function getLlmSettings(): Promise<LlmSettings> {
  return requestJson<LlmSettings>("/api/settings/llm");
}

export async function testLlm(): Promise<LlmTestResult> {
  return requestJson<LlmTestResult>("/api/settings/llm/test", {
    method: "POST",
  });
}

export async function getLlmLogs(): Promise<LlmCallLog[]> {
  return requestJson<LlmCallLog[]>("/api/llm-logs");
}

export async function getLlmLog(logId: string): Promise<LlmCallLog> {
  return requestJson<LlmCallLog>(`/api/llm-logs/${logId}`);
}

export async function generateTaskFileChunks(taskFileId: string): Promise<DocumentChunk[]> {
  return requestJson<DocumentChunk[]>(`/api/task-files/${taskFileId}/chunks`, {
    method: "POST",
  });
}

export async function getTaskFileChunks(taskFileId: string): Promise<DocumentChunk[]> {
  return requestJson<DocumentChunk[]>(`/api/task-files/${taskFileId}/chunks`);
}

export async function getRetrievalSettings(): Promise<RetrievalSettings> {
  return requestJson<RetrievalSettings>("/api/settings/retrieval");
}

export async function updateRetrievalSettings(payload: RetrievalSettingsUpdate): Promise<RetrievalSettings> {
  return requestJson<RetrievalSettings>("/api/settings/retrieval", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function retrieveTaskFiles(
  taskId: string,
  payload: { question: string; retrieval_mode?: RetrievalMode; top_k?: number },
): Promise<RetrieveResponse> {
  return requestJson<RetrieveResponse>(`/api/tasks/${taskId}/retrieve`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function askTaskQuestion(taskId: string, questionText: string): Promise<Answer> {
  return requestJson<Answer>(`/api/tasks/${taskId}/ask`, {
    method: "POST",
    body: JSON.stringify({ question_text: questionText }),
  });
}

export async function getTaskResults(taskId: string): Promise<Answer[]> {
  return requestJson<Answer[]>(`/api/tasks/${taskId}/results`);
}

export async function getAnswer(answerId: string): Promise<Answer> {
  return requestJson<Answer>(`/api/answers/${answerId}`);
}

export async function analyzeExcelTaskFile(
  taskFileId: string,
  payload: { question: string; sheet_name?: string | null; agent_run_id?: string | null; iteration_id?: string | null },
): Promise<ExcelAnalyzeResponse> {
  return requestJson<ExcelAnalyzeResponse>(`/api/task-files/${taskFileId}/excel/analyze`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getTaskCapabilityCheck(taskId: string): Promise<CapabilityCheck> {
  return requestJson<CapabilityCheck>(`/api/tasks/${taskId}/capability-check`);
}

export async function getPhase0Requirements(): Promise<Phase0Requirements> {
  return requestJson<Phase0Requirements>("/api/phase0/requirements");
}

export async function startAgentRun(
  taskId: string,
  payload: { question: string; max_iterations: number },
): Promise<AgentRunStartResponse> {
  return requestJson<AgentRunStartResponse>(`/api/tasks/${taskId}/agent-runs`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getAgentRun(runId: string): Promise<AgentRun> {
  return requestJson<AgentRun>(`/api/agent-runs/${runId}`);
}
