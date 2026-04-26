import ParsingClient from "./ParsingClient";

export default async function ParsingPage({
  params,
}: {
  params: Promise<{ taskId: string }>;
}) {
  const { taskId } = await params;
  return <ParsingClient taskId={taskId} />;
}
