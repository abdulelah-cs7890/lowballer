import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { ArrowLeft, ExternalLink } from "lucide-react";
import { Link } from "@/i18n/navigation";
import { fetchDeal } from "@/lib/api";
import { money } from "@/lib/format";
import DiscountBadge from "@/components/DiscountBadge";
import ValuationBar from "@/components/ValuationBar";

export const dynamic = "force-dynamic";

export default async function DealPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  const deal = await fetchDeal(id);
  if (!deal) notFound();

  const t = await getTranslations();
  const sar = t("units.sar");
  const km = t("units.km");
  const enumLabel = (ns: string, v: string | null) =>
    v && t.has(`enums.${ns}.${v}`) ? t(`enums.${ns}.${v}`) : (v ?? "—");

  const specs: [string, string][] = [
    [t("specs.mileage"), deal.mileage_km != null ? `${money(deal.mileage_km)} ${km}` : "—"],
    [t("specs.year"), deal.year ? String(deal.year) : "—"],
    [t("specs.engine"), deal.engine_size ? `${deal.engine_size}L` : "—"],
    [t("specs.fuel"), enumLabel("fuel", deal.fuel_type)],
    [t("specs.gear"), enumLabel("gear", deal.gear_type)],
    [t("specs.origin"), enumLabel("origin", deal.origin)],
    [t("specs.region"), enumLabel("region", deal.region)],
    [t("specs.options"), enumLabel("options", deal.options)],
  ];

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <Link href="/" className="inline-flex items-center gap-1.5 text-sm text-accent hover:underline">
        <ArrowLeft className="h-4 w-4 rtl:-scale-x-100" /> {t("deal.back")}
      </Link>

      <div className="mt-4 flex items-start justify-between gap-4">
        <h1 className="font-display text-3xl font-bold text-white">
          {deal.year} {deal.make} {deal.model}
        </h1>
        <DiscountBadge percent={deal.percent_below} needsReview={deal.needs_review} />
      </div>

      {deal.needs_review && (
        <p className="card mt-4 border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-200">
          ⚠ {t("deal.reviewBanner")}
        </p>
      )}

      <section className="card mt-6 p-6">
        <div className="max-w-md">
          <ValuationBar asking={deal.asking_price} predicted={deal.predicted_price} big />
        </div>
        {deal.url && (
          <a
            href={deal.url}
            target="_blank"
            rel="noreferrer"
            className="mt-5 inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-ink-950 transition hover:bg-accent-soft"
          >
            {t("deal.viewOriginal")} <ExternalLink className="h-4 w-4 rtl:-scale-x-100" />
          </a>
        )}
      </section>

      <section className="card mt-6 p-6">
        <h2 className="mb-4 font-display text-lg font-semibold text-white">{t("deal.specs")}</h2>
        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {specs.map(([label, value]) => (
            <div key={label} className="rounded-xl border border-ink-800 bg-ink-850 px-3 py-2.5">
              <dt className="text-[11px] uppercase tracking-wide text-slate-500">{label}</dt>
              <dd className="mt-0.5 text-sm font-medium text-slate-100">{value}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="card mt-6 p-6">
        <h2 className="font-display text-lg font-semibold text-white">{t("deal.whyWorthMore")}</h2>
        <p className="mb-4 mt-1 text-sm text-slate-400">{t("deal.comparable", { make: deal.make ?? "" })}</p>
        {deal.comps.length === 0 ? (
          <p className="text-sm text-slate-500">{t("deal.noComps")}</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-ink-800 text-slate-500">
                <th className="py-2 text-start font-medium">{t("deal.car")}</th>
                <th className="py-2 text-start font-medium">{t("deal.mileage")}</th>
                <th className="py-2 text-end font-medium">{t("deal.asking")}</th>
              </tr>
            </thead>
            <tbody>
              {deal.comps.map((c, i) => (
                <tr key={i} className="border-b border-ink-800/60 last:border-0">
                  <td className="py-2.5 text-slate-200">
                    {c.year} {c.make} {c.model}
                  </td>
                  <td className="py-2.5 text-slate-400">
                    {c.mileage_km != null ? `${money(c.mileage_km)} ${km}` : "—"}
                  </td>
                  <td className="py-2.5 text-end font-medium text-slate-100">
                    {money(c.asking_price)} {sar}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </main>
  );
}
