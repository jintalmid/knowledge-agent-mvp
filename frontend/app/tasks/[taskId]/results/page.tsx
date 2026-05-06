import ResultsClient from "./ResultsClient";

export default async function ResultsPage({
  params,
  searchParams,
}: {
  params: Promise<{ taskId: string }>;
  searchParams: Promise<{ answerId?: string | string[] }>;
}) {
  const { taskId } = await params;
  const { answerId } = await searchParams;
  const initialAnswerId = Array.isArray(answerId) ? (answerId[0] ?? null) : (answerId ?? null);

  return <ResultsClient initialAnswerId={initialAnswerId} taskId={taskId} />;
}
