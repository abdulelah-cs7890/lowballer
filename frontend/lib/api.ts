export type Deal = {
  id: string;
  make: string | null; // product category (GPU, Phone, …)
  model: string | null; // product model (RTX 4090, …)
  url: string | null;
  title: string | null;
  image: string | null;
  condition: string | null;
  asking_price: number;
  predicted_price: number; // comps median (fair value)
  percent_below: number;
  needs_review: boolean;
};

export type Comp = {
  make: string | null;
  model: string | null;
  title: string | null;
  condition: string | null;
  asking_price: number;
};

export type DealDetail = Deal & {
  comps: Comp[];
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function fetchDeals(opts: {
  make?: string;
  minPercentBelow?: number;
  limit?: number;
} = {}): Promise<Deal[]> {
  const qs = new URLSearchParams();
  if (opts.make) qs.set("make", opts.make);
  if (opts.minPercentBelow) qs.set("min_percent_below", String(opts.minPercentBelow));
  qs.set("limit", String(opts.limit ?? 60));

  const res = await fetch(`${API}/deals?${qs.toString()}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API ${res.status} fetching deals`);
  return res.json();
}

export async function fetchDeal(id: string): Promise<DealDetail | null> {
  const res = await fetch(`${API}/deals/${id}`, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`API ${res.status} fetching deal ${id}`);
  return res.json();
}
