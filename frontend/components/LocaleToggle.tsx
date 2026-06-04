"use client";

import { useLocale } from "next-intl";
import { usePathname, useRouter } from "@/i18n/navigation";
import { routing } from "@/i18n/routing";

/** EN | AR pills. Switching keeps the current path (e.g. a deal detail). */
export default function LocaleToggle() {
  const locale = useLocale();
  const pathname = usePathname();
  const router = useRouter();

  return (
    <div className="inline-flex overflow-hidden rounded-full border border-ink-700">
      {routing.locales.map((l) => (
        <button
          key={l}
          onClick={() => router.replace(pathname, { locale: l })}
          aria-pressed={l === locale}
          className={`px-3 py-1.5 text-xs font-bold uppercase transition ${
            l === locale ? "bg-accent text-ink-950" : "text-slate-300 hover:bg-ink-800"
          }`}
        >
          {l}
        </button>
      ))}
    </div>
  );
}
