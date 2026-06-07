import "../globals.css";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { NextIntlClientProvider } from "next-intl";
import { getMessages, getTranslations, setRequestLocale } from "next-intl/server";
import { Space_Grotesk, IBM_Plex_Sans_Arabic } from "next/font/google";
import { routing, type Locale } from "@/i18n/routing";
import Header from "@/components/Header";
import { DealsStreamProvider } from "@/components/DealsStream";
import Toaster from "@/components/Toaster";

const display = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});
const arabic = IBM_Plex_Sans_Arabic({
  subsets: ["arabic"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-arabic",
  display: "swap",
});

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "meta" });
  return { title: t("title"), description: t("description") };
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!routing.locales.includes(locale as Locale)) notFound();
  setRequestLocale(locale);
  const messages = await getMessages();
  const dir = locale === "ar" ? "rtl" : "ltr";

  return (
    <html lang={locale} dir={dir} className={`${display.variable} ${arabic.variable}`}>
      <body>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <DealsStreamProvider>
            <Header />
            {children}
            <Toaster />
          </DealsStreamProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
