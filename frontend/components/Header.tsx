import { getTranslations } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import LocaleToggle from "./LocaleToggle";
import NotificationBell from "./NotificationBell";

export default async function Header() {
  const t = await getTranslations("header");
  return (
    <header className="sticky top-0 z-20 border-b border-ink-800 bg-ink-950/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-3">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="grid h-7 w-7 place-items-center rounded-md bg-accent font-display text-sm font-bold text-ink-950">
            ◆
          </span>
          <span className="flex flex-col leading-none">
            <span className="font-display text-sm font-bold tracking-wide text-white">LOWBALLER</span>
            <span className="mt-1 text-[11px] text-slate-400">{t("tagline")}</span>
          </span>
        </Link>
        <div className="flex items-center gap-2.5">
          <NotificationBell />
          <LocaleToggle />
        </div>
      </div>
    </header>
  );
}
