import SummariesClient from "./SummariesClient";

export default async function SummariesPage({
  params,
}: {
  params: Promise<{ taskId: string }>;
}) {
  const { taskId } = await params;
  return <SummariesClient taskId={taskId} />;
}
