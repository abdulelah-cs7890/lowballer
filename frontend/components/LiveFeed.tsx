"use client";

import { useTranslations } from "next-intl";
import DealCard from "./DealCard";
import { useDealsStream } from "./DealsStream";

/** Dashboard "new deals" row — shares the app-wide SSE connection (see DealsStream). */
export default function LiveFeed() {
  const t = useTranslations("live");
  const { deals, connected } = useDealsStream();
  const fresh = deals.slice(0, 9);

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
        <span className="text-slate-500">{fresh.length > 0 ? t("newDeals") : t("waiting")}</span>
      </div>

      {fresh.length > 0 && (
        <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {fresh.map((d) => (
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
