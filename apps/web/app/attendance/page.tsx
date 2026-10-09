import type { Metadata } from "next";
import { AttendanceWeb } from "@/components/attendance-web";
export const metadata: Metadata = { title: "Rodada Atendimento", manifest: "/attendance/manifest.webmanifest" };
export default function AttendancePage() { return <AttendanceWeb />; }
