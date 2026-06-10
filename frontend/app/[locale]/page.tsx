import { getTranslations, setRequestLocale } from "next-intl/server";
import { fetchDeals, type Deal } from "@/lib/api";
import DealCard from "@/components/DealCard";
import Filters from "@/components/Filters";
import LiveFeed from "@/components/LiveFeed";

export const dynamic = "force-dynamic";
export const maxDuration = 60; // tolerate a cold (spun-down) backend on first load

export default async function Home({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ make?: string; min?: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const sp = await searchParams;
  const make = sp.make?.trim() ?? "";
  const minPct = sp.min ? Number(sp.min) : 0;
  const t = await getTranslations();

  let deals: Deal[];
  let error: string | null = null;
  try {
    deals = await fetchDeals({
      make: make || undefined,
      minPercentBelow: minPct ? minPct / 100 : undefined,
    });
  } catch (e) {
    error = (e as Error).message;
    deals = [];
  }

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold text-white">{t("deals.title")}</h1>
          <p className="mt-2 text-sm text-slate-400">{t("deals.subtitle")}</p>
        </div>
        <Filters make={make} minPct={minPct} />
      </div>

      <LiveFeed />

      {error ? (
        <p className="card p-4 text-rose-300">{t("deals.apiError", { error })}</p>
      ) : deals.length === 0 ? (
        <p className="text-slate-400">{t("deals.none")}</p>
      ) : (
        <>
          <p className="mb-4 text-sm text-slate-500">{t("deals.count", { count: deals.length })}</p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {deals.map((d) => (
              <DealCard key={d.id} deal={d} />
            ))}
          </div>
        </>
      )}
    </main>
  );
}
