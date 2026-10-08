import type { Metadata } from "next";
import { ProductionBoard } from "@/components/production-board";

export const metadata: Metadata = { title: "Rodada Bar" };

export default function BarPage() { return <ProductionBoard station="BAR" title="Bar" />; }
