import { getTranslations } from "next-intl/server";
import { Link } from "@/i18n/navigation";

export default async function NotFound() {
  const t = await getTranslations("deal");
  return (
    <main className="mx-auto max-w-4xl px-6 py-24 text-center">
      <p className="font-display text-6xl font-bold text-accent">404</p>
      <Link
        href="/"
        className="mt-6 inline-block text-sm text-slate-300 transition hover:text-accent hover:underline"
      >
        {t("back")}
      </Link>
    </main>
  );
}
