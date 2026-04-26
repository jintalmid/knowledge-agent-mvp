import AgentRunClient from "./AgentRunClient";

export default async function AgentRunPage({
  params,
}: {
  params: Promise<{ taskId: string; runId: string }>;
}) {
  const { taskId, runId } = await params;
  return <AgentRunClient runId={runId} taskId={taskId} />;
}
