"use client";

import { useLocale, useTranslations } from "next-intl";

const inputCls =
  "rounded-lg border border-ink-700 bg-ink-900 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:border-accent focus:outline-none";

export default function Filters({ make, minPct }: { make: string; minPct: number }) {
  const t = useTranslations("filters");
  const locale = useLocale();
  return (
    <form className="flex flex-wrap items-end gap-3" action={`/${locale}`} method="get">
      <label className="flex flex-col text-xs">
        <span className="mb-1.5 font-medium text-slate-400">{t("make")}</span>
        <input name="make" defaultValue={make} placeholder={t("makePlaceholder")} className={inputCls} />
      </label>
      <label className="flex flex-col text-xs">
        <span className="mb-1.5 font-medium text-slate-400">{t("minBelow")}</span>
        <input
          name="min"
          type="number"
          min={0}
          max={100}
          defaultValue={minPct || ""}
          placeholder={t("minPlaceholder")}
          className={`w-32 ${inputCls}`}
        />
      </label>
      <button className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-ink-950 transition hover:bg-accent-soft">
        {t("apply")}
      </button>
    </form>
  );
}
