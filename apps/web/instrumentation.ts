/**
 * Next.js OpenTelemetry setup. Server-side fetches to the commerce API carry the W3C trace
 * context, so a page render and the API work it causes form one trace. Exports go to
 * OTEL_EXPORTER_OTLP_ENDPOINT (the local collector in development).
 */
export async function register() {
  if (process.env.NEXT_RUNTIME !== "nodejs") return;
  const { registerOTel } = await import("@vercel/otel");
  const { PeriodicExportingMetricReader } = await import("@opentelemetry/sdk-metrics");
  const { OTLPMetricExporter } = await import("@opentelemetry/exporter-metrics-otlp-http");

  const apiUrl = process.env.COMMERCE_API_URL ?? "http://localhost:8000";
  const endpoint = process.env.OTEL_EXPORTER_OTLP_ENDPOINT;
  registerOTel({
    serviceName: "web",
    attributes: { "deployment.environment.name": process.env.APP_ENV ?? "dev" },
    instrumentationConfig: {
      fetch: { propagateContextUrls: [apiUrl] },
    },
    metricReaders: endpoint
      ? [
          new PeriodicExportingMetricReader({
            exporter: new OTLPMetricExporter({ url: `${endpoint.replace(/\/$/, "")}/v1/metrics` }),
            exportIntervalMillis: 15000,
          }),
        ]
      : [],
  });
}
