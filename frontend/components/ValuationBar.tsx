"use client";

import { useTranslations } from "next-intl";
import { money } from "@/lib/format";

/** Horizontal bar: asking price as a fraction of the model's fair value. */
export default function ValuationBar({
  asking,
  predicted,
  big = false,
}: {
  asking: number;
  predicted: number;
  big?: boolean;
}) {
  const t = useTranslations();
  const sar = t("units.sar");
  const ratio = predicted > 0 ? Math.min(1, asking / predicted) : 1;

  return (
    <div>
      <div className="flex items-center justify-between text-[11px] uppercase tracking-wide text-slate-500">
        <span>{t("valuation.asking")}</span>
        <span>{t("valuation.fair")}</span>
      </div>
      <div className={`mt-1.5 w-full overflow-hidden rounded-full bg-ink-800 ${big ? "h-3" : "h-2"}`}>
        <div
          className="h-full rounded-full bg-accent transition-[width] duration-500"
          style={{ width: `${ratio * 100}%` }}
        />
      </div>
      <div className={`mt-1.5 flex items-baseline justify-between ${big ? "text-base" : "text-sm"}`}>
        <span className="font-display font-bold text-accent">
          {money(asking)} {sar}
        </span>
        <span className="text-xs text-slate-500 line-through">
          {money(predicted)} {sar}
        </span>
      </div>
    </div>
  );
}
