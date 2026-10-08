import type { Metadata } from "next";
import { ProductionBoard } from "@/components/production-board";

export const metadata: Metadata = { title: "Rodada Cozinha" };

export default function KitchenPage() { return <ProductionBoard station="KITCHEN" title="Cozinha" />; }
