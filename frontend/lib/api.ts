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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

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
