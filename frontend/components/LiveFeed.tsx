"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import type { Deal } from "@/lib/api";
import DealCard from "./DealCard";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Subscribes to the SSE stream and surfaces newly flagged deals live, no refresh. */
export default function LiveFeed() {
  const t = useTranslations("live");
  const [deals, setDeals] = useState<Deal[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const es = new EventSource(`${API}/deals/stream`);
    es.onopen = () => setConnected(true);
    es.onerror = () => setConnected(false);
    es.onmessage = (e) => {
      try {
        const deal = JSON.parse(e.data) as Deal;
        setDeals((prev) =>
          prev.some((d) => d.id === deal.id) ? prev : [deal, ...prev].slice(0, 9),
        );
      } catch {
        /* ignore malformed frames */
      }
    };
    return () => es.close();
  }, []);

  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 text-xs font-medium">
        <span className="relative flex h-2 w-2">
          {connected && (
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-75" />
          )}
          <span
            className={`relative inline-flex h-2 w-2 rounded-full ${connected ? "bg-accent" : "bg-slate-600"}`}
          />
        </span>
        <span className={connected ? "text-accent" : "text-slate-500"}>{t("indicator")}</span>
        <span className="text-slate-500">·</span>
        <span className="text-slate-500">
          {deals.length > 0 ? t("newDeals") : t("waiting")}
        </span>
      </div>

      {deals.length > 0 && (
        <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {deals.map((d) => (
            <div key={d.id} className="animate-in-up relative rounded-2xl ring-1 ring-accent/40">
              <span className="absolute -top-2 end-3 z-10 rounded-full bg-accent px-2 py-0.5 text-[10px] font-bold text-ink-950">
                {t("new")}
              </span>
              <DealCard deal={d} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
