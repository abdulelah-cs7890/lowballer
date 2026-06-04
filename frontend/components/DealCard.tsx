"use client";

import { useTranslations } from "next-intl";
import { Gauge, MapPin } from "lucide-react";
import { Link } from "@/i18n/navigation";
import type { Deal } from "@/lib/api";
import { money } from "@/lib/format";
import DiscountBadge from "./DiscountBadge";
import ValuationBar from "./ValuationBar";

export default function DealCard({ deal }: { deal: Deal }) {
  const t = useTranslations();
  const saving = deal.predicted_price - deal.asking_price;
  const region =
    deal.region && t.has(`enums.region.${deal.region}`)
      ? t(`enums.region.${deal.region}`)
      : (deal.region ?? "—");

  return (
    <Link
      href={`/deal/${deal.id}`}
      className="group card block p-5 transition duration-200 hover:-translate-y-0.5 hover:border-accent/40 hover:glow"
    >
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-display text-lg font-semibold text-white">
          {deal.year} {deal.make} {deal.model}
        </h3>
        <DiscountBadge percent={deal.percent_below} needsReview={deal.needs_review} />
      </div>

      <p className="mt-1 text-xs font-medium text-accent/80">
        {t("deals.belowFairValue", { amount: `${money(saving)} ${t("units.sar")}` })}
      </p>

      <div className="mt-4">
        <ValuationBar asking={deal.asking_price} predicted={deal.predicted_price} />
      </div>

      <div className="mt-4 flex items-center gap-4 text-xs text-slate-400">
        <span className="inline-flex items-center gap-1.5">
          <Gauge className="h-3.5 w-3.5" />
          {deal.mileage_km != null ? `${money(deal.mileage_km)} ${t("units.km")}` : "—"}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <MapPin className="h-3.5 w-3.5" />
          {region}
        </span>
      </div>
    </Link>
  );
}
