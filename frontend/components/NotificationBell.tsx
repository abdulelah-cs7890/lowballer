"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Bell } from "lucide-react";
import { Link } from "@/i18n/navigation";
import { money, pctNum } from "@/lib/format";
import { useDealsStream } from "./DealsStream";

export default function NotificationBell() {
  const t = useTranslations();
  const { deals, unread, connected, markAllRead } = useDealsStream();
  const [open, setOpen] = useState(false);

  const toggle = () => {
    if (!open) markAllRead();
    setOpen((o) => !o);
  };

  return (
    <div className="relative">
      <button
        onClick={toggle}
        aria-label={t("notifications.title")}
        className="relative grid h-8 w-8 place-items-center rounded-full border border-ink-700 text-slate-300 transition hover:bg-ink-800"
      >
        <Bell className="h-4 w-4" />
        {unread > 0 && (
          <span className="absolute -end-1.5 -top-1.5 grid h-4 min-w-[1rem] place-items-center rounded-full bg-accent px-1 text-[10px] font-bold text-ink-950">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-30" onClick={() => setOpen(false)} />
          <div className="absolute end-0 z-40 mt-2 w-80 max-w-[calc(100vw-2rem)] overflow-hidden rounded-xl border border-ink-800 bg-ink-900 shadow-2xl">
            <div className="flex items-center justify-between border-b border-ink-800 px-3 py-2">
              <span className="text-sm font-semibold text-white">{t("notifications.title")}</span>
              <span className="flex items-center gap-1.5 text-[11px] text-slate-500">
                <span className={`h-1.5 w-1.5 rounded-full ${connected ? "bg-accent" : "bg-slate-600"}`} />
                {connected ? t("notifications.live") : t("notifications.offline")}
              </span>
            </div>
            {deals.length === 0 ? (
              <p className="px-3 py-8 text-center text-sm text-slate-500">{t("notifications.empty")}</p>
            ) : (
              <ul className="max-h-80 overflow-y-auto">
                {deals.map((d) => (
                  <li key={d.id}>
                    <Link
                      href={`/deal/${d.id}`}
                      onClick={() => setOpen(false)}
                      className="block px-3 py-2.5 transition hover:bg-ink-800"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                          {d.make}
                        </span>
                        <span className="rounded-full bg-accent/15 px-1.5 py-0.5 text-[10px] font-bold text-accent">
                          {t("badge.below", { pct: pctNum(d.percent_below) })}
                        </span>
                      </div>
                      <p className="mt-0.5 line-clamp-1 text-sm text-slate-200">{d.title}</p>
                      <p className="font-display text-xs font-semibold text-accent">
                        {money(d.asking_price)} {t("units.sar")}
                      </p>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </div>
  );
}
