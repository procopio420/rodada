import { notFound } from "next/navigation";
import { DeveloperStaff } from "@/components/developer-staff";
export const dynamic = "force-dynamic";
export default function DeveloperStaffPage() {
  if (process.env.RODADA_DEVELOPER_TOOLS !== "true") notFound();
  return <DeveloperStaff />;
}
