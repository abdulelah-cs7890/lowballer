"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import type { Deal } from "@/lib/api";
import { money } from "@/lib/format";
import DiscountBadge from "./DiscountBadge";
import ValuationBar from "./ValuationBar";

export default function DealCard({ deal }: { deal: Deal }) {
  const t = useTranslations();
  const saving = deal.predicted_price - deal.asking_price;

  return (
    <Link
      href={`/deal/${deal.id}`}
      className="group card block p-4 transition duration-200 hover:-translate-y-0.5 hover:border-accent/40 hover:glow"
    >
      <div className="flex gap-4">
        <div className="h-20 w-20 shrink-0 overflow-hidden rounded-lg bg-ink-800">
          {deal.image && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={deal.image} alt="" className="h-full w-full object-cover" />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <span className="rounded bg-ink-800 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-400">
              {deal.make}
            </span>
            <DiscountBadge percent={deal.percent_below} needsReview={deal.needs_review} />
          </div>
          <h3 className="mt-1.5 line-clamp-2 text-sm font-semibold text-white">{deal.title}</h3>
          <p className="mt-0.5 truncate text-xs text-slate-500">
            {deal.model}
            {deal.condition ? ` · ${deal.condition}` : ""}
          </p>
        </div>
      </div>

      <p className="mt-2 text-xs font-medium text-accent/80">
        {t("deals.belowFairValue", { amount: `${money(saving)} ${t("units.sar")}` })}
      </p>
      <div className="mt-3">
        <ValuationBar asking={deal.asking_price} predicted={deal.predicted_price} />
      </div>
    </Link>
  );
}
