"use client";

import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { X } from "lucide-react";
import { Link } from "@/i18n/navigation";
import type { Deal } from "@/lib/api";
import { money, pctNum } from "@/lib/format";
import { useDealsStream } from "./DealsStream";

const TTL = 7000;

export default function Toaster() {
  const t = useTranslations();
  const { deals } = useDealsStream();
  const [toasts, setToasts] = useState<Deal[]>([]);
  const toasted = useRef<Set<string>>(new Set());

  useEffect(() => {
    const fresh = deals.filter((d) => !toasted.current.has(d.id));
    if (fresh.length === 0) return;
    fresh.forEach((d) => toasted.current.add(d.id));
    setToasts((cur) => [...fresh, ...cur].slice(0, 3));
    fresh.forEach((d) =>
      setTimeout(() => setToasts((cur) => cur.filter((x) => x.id !== d.id)), TTL),
    );
  }, [deals]);

  if (toasts.length === 0) return null;

  return (
    <div className="pointer-events-none fixed bottom-4 end-4 z-50 flex w-80 max-w-[calc(100vw-2rem)] flex-col gap-2">
      {toasts.map((d) => (
        <Link
          key={d.id}
          href={`/deal/${d.id}`}
          onClick={() => setToasts((cur) => cur.filter((x) => x.id !== d.id))}
          className="animate-in-up card pointer-events-auto block p-3 ring-1 ring-accent/40 glow"
        >
          <div className="flex items-start justify-between gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wide text-accent">
              ⚡ {t("notifications.newDeal")}
            </span>
            <button
              onClick={(e) => {
                e.preventDefault();
                setToasts((cur) => cur.filter((x) => x.id !== d.id));
              }}
              className="text-slate-500 hover:text-slate-300"
              aria-label="dismiss"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
          <p className="mt-1 line-clamp-1 text-sm font-semibold text-white">{d.title}</p>
          <p className="mt-0.5 text-xs text-slate-400">
            <span className="font-display font-bold text-accent">
              {money(d.asking_price)} {t("units.sar")}
            </span>{" "}
            · {t("badge.below", { pct: pctNum(d.percent_below) })}
          </p>
        </Link>
      ))}
    </div>
  );
}
