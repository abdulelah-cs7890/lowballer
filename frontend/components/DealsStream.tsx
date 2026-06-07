"use client";

import { createContext, useContext, useEffect, useRef, useState } from "react";
import type { Deal } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type DealsStream = {
  deals: Deal[]; // new deals received this session, newest first
  connected: boolean;
  unread: number;
  markAllRead: () => void;
};

const Ctx = createContext<DealsStream>({
  deals: [],
  connected: false,
  unread: 0,
  markAllRead: () => {},
});

/** Opens ONE SSE connection for the whole app; the live row, bell, and toasts share it. */
export function DealsStreamProvider({ children }: { children: React.ReactNode }) {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [connected, setConnected] = useState(false);
  const [unread, setUnread] = useState(0);
  const seen = useRef<Set<string>>(new Set());

  useEffect(() => {
    const es = new EventSource(`${API}/deals/stream`);
    es.onopen = () => setConnected(true);
    es.onerror = () => setConnected(false);
    es.onmessage = (e) => {
      try {
        const deal = JSON.parse(e.data) as Deal;
        if (seen.current.has(deal.id)) return;
        seen.current.add(deal.id);
        setDeals((prev) => [deal, ...prev].slice(0, 30));
        setUnread((u) => u + 1);
      } catch {
        /* ignore malformed frames */
      }
    };
    return () => es.close();
  }, []);

  return (
    <Ctx.Provider value={{ deals, connected, unread, markAllRead: () => setUnread(0) }}>
      {children}
    </Ctx.Provider>
  );
}

export const useDealsStream = () => useContext(Ctx);
