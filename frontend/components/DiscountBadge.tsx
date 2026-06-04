"use client";

import { useTranslations } from "next-intl";
import { pctNum } from "@/lib/format";

export default function DiscountBadge({
  percent,
  needsReview = false,
}: {
  percent: number;
  needsReview?: boolean;
}) {
  const t = useTranslations("badge");
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="rounded-full bg-accent/15 px-2.5 py-1 text-xs font-bold text-accent ring-1 ring-accent/30">
        {t("below", { pct: pctNum(percent) })}
      </span>
      {needsReview && (
        <span
          title={t("reviewTooltip")}
          className="rounded-full bg-amber-500/15 px-2 py-1 text-[11px] font-medium text-amber-300 ring-1 ring-amber-500/30"
        >
          ⚠ {t("review")}
        </span>
      )}
    </span>
  );
}
