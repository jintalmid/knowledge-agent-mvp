import ResultsClient from "./ResultsClient";

export default async function ResultsPage({
  params,
}: {
  params: Promise<{ taskId: string }>;
}) {
  const { taskId } = await params;
  return <ResultsClient taskId={taskId} />;
}
