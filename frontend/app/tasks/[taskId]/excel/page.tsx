import ExcelClient from "./ExcelClient";

export default async function ExcelPage({
  params,
}: {
  params: Promise<{ taskId: string }>;
}) {
  const { taskId } = await params;
  return <ExcelClient taskId={taskId} />;
}
