import AskClient from "./AskClient";

export default async function AskPage({
  params,
}: {
  params: Promise<{ taskId: string }>;
}) {
  const { taskId } = await params;
  return <AskClient taskId={taskId} />;
}
