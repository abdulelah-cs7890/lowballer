import { createNavigation } from "next-intl/navigation";
import { routing } from "./routing";

// Locale-aware navigation: these keep the active locale prefix automatically.
export const { Link, redirect, usePathname, useRouter, getPathname } =
  createNavigation(routing);
