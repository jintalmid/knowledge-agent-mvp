import RetrievalClient from "./RetrievalClient";

export default async function RetrievalPage({
  params,
}: {
  params: Promise<{ taskId: string }>;
}) {
  const { taskId } = await params;
  return <RetrievalClient taskId={taskId} />;
}
