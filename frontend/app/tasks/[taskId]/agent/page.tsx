import AgentClient from "./AgentClient";

export default async function AgentPage({
  params,
}: {
  params: Promise<{ taskId: string }>;
}) {
  const { taskId } = await params;
  return <AgentClient taskId={taskId} />;
}
