import TaskFilesClient from "./TaskFilesClient";

export default async function TaskFilesPage({
  params,
}: {
  params: Promise<{ taskId: string }>;
}) {
  const { taskId } = await params;
  return <TaskFilesClient taskId={taskId} />;
}
