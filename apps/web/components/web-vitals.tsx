"use client";

import { useEffect } from "react";
import { onINP, onLCP, type Metric } from "web-vitals";

/** Report real-browser LCP and INP to /vitals, which records them as OTel metrics. */
export function WebVitalsReporter({ route }: { route: string }) {
  useEffect(() => {
    const send = (metric: Metric) => {
      const body = JSON.stringify({ name: metric.name, value: metric.value, route });
      if (!navigator.sendBeacon?.("/vitals", body)) {
        void fetch("/vitals", { method: "POST", body, keepalive: true });
      }
    };
    onLCP(send);
    onINP(send);
  }, [route]);
  return null;
}
