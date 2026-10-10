/**
 * The assistant API's shapes (services/assistant/src/assistant/schemas.py). Cards come from
 * tool results on the server, never from the model's text, so their prices and statuses are
 * what the commerce API returned.
 */

export type AgentName = "steph" | "xana";

export type Tag = { value: string; label: string };

export type ProductCard = {
  kind: "product";
  id: string;
  title: string;
  brand: string;
  product_type: string;
  price_minor: number;
  currency: string;
  image_path: string;
  in_stock: boolean;
  tags: Tag[];
  url: string;
  variant_id: string | null;
  variant_name: string | null;
  facts: string[];
  /** Customer reviews (absent on cards saved before 2026-10-10). */
  rating_average?: number | null;
  rating_count?: number;
};

export type OrderCard = {
  kind: "order";
  id: string;
  number: string;
  status: string;
  placed_at: string;
  delivered_at: string | null;
  total_minor: number;
  currency: string;
  item_count: number;
  lines: { id: string; title: string; variant_name: string; quantity: number; image_path: string }[];
  url: string;
};

export type StoreCard = {
  kind: "store";
  code: string;
  name: string;
  address: string;
  phone: string;
  open_now: boolean;
  today_hours: string;
  services: string[];
  directions_url: string;
};

export type CitationCard = {
  kind: "citation";
  cite: string;
  doc_title: string;
  number: string;
  title: string;
  version: string;
  url: string | null;
  excerpt: string;
};

export type CartCard = {
  kind: "cart";
  added_title: string;
  added_variant: string;
  quantity: number;
  item_count: number;
  subtotal_minor: number;
  currency: string;
};

/** What's in the cart now (Xena reads it; she can't change it). */
export type CartSummaryCard = {
  kind: "cart_summary";
  item_count: number;
  lines: {
    title: string;
    variant_name: string;
    quantity: number;
    line_total_minor: number;
    image_path: string;
    in_stock: boolean;
    url: string;
  }[];
  more_lines: number;
  subtotal_minor: number;
  shipping_minor: number;
  estimated_total_minor: number;
  free_shipping_remaining_minor: number;
  currency: string;
  url: string;
};

export type SupportCasesCard = {
  kind: "support_cases";
  cases: {
    reference: string;
    topic: string;
    status: string;
    status_label: string;
    opened_at: string;
    order_number: string | null;
    order_url: string | null;
    reply_within: string | null;
  }[];
  total: number;
  url: string;
};

export type ActivityCard = {
  kind: "activity";
  events: {
    what: string;
    type: string;
    occurred_at: string;
    product_title: string | null;
    product_url: string | null;
    image_path: string | null;
    order_number: string | null;
    order_url: string | null;
    detail: string | null;
    is_sample: boolean;
  }[];
  url: string;
};

export type HandoffCard = { kind: "handoff"; reason: string; message: string };

export type ReturnOptionsCard = {
  kind: "return_options";
  order_id: string;
  lines: {
    order_line_id: string;
    title: string;
    variant_name: string;
    image_path: string;
    eligible: boolean;
    returnable_quantity: number;
    max_refund_minor: number;
    message: string;
  }[];
};

export type ReturnStatusCard = {
  kind: "return_status";
  outcome: "confirmed" | "declined" | "expired" | "superseded" | "existing";
  rma_number?: string | null;
  status?: string | null;
  refund_minor?: number | null;
  refund_status?: string | null;
  needs_shipping?: boolean;
  return_id?: string;
  items?: string[];
};

/** A priced return waiting for the customer's own confirmation. `readback` is built by code. */
export type ReturnQuoteCard = {
  kind: "return_quote";
  quote_id: string;
  order_id: string;
  status: "open" | "expired" | "confirmed";
  lines: {
    order_line_id: string;
    title: string;
    variant_name: string;
    image_path: string;
    quantity: number;
    refund_minor: number;
    refund_timing: string;
    timing_message: string;
  }[];
  items_refund_minor: number;
  shipping_refund_minor: number;
  total_refund_minor: number;
  currency: string;
  refund_destination: string;
  needs_shipping: boolean;
  expires_at: string;
  policy_version: string;
  readback: string;
};

export type SearchCard = { kind: "search"; total: number; shown: number; chips: string[]; url: string };

export type XanaCard = { kind: "xana"; about: string; message: string; url: string };

export type Card =
  | SearchCard
  | XanaCard
  | ProductCard
  | OrderCard
  | StoreCard
  | CartCard
  | CartSummaryCard
  | SupportCasesCard
  | ActivityCard
  | HandoffCard
  | ReturnOptionsCard
  | ReturnStatusCard;

export type SignalPick = { value: string; confidence: number; act: boolean };

/** Jev's typed read of a customer turn (services/assistant/src/assistant/jev/decisions.py). */
export type TurnSignals = {
  source: "jev" | "simulated" | "off" | "error";
  model: string | null;
  latency_ms: number;
  intent: SignalPick | null;
  return_reason: SignalPick | null;
  target_line: SignalPick | null;
  wants_person: number | null;
  frustration: number | null;
  policy_bypass: number | null;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  cards: Card[];
  citations: CitationCard[];
  /** Still streaming: citation markers aren't resolved yet. */
  pending?: boolean;
  /** Tool activity shown while the answer is being prepared. */
  status?: string | null;
  error?: string | null;
  /** Development only: why the answer took its route. */
  signals?: TurnSignals | null;
  /** A return quote this answer is waiting on the customer to confirm or decline. */
  quote?: ReturnQuoteCard | null;
};

export type Conversation = {
  id: string;
  agent: AgentName;
  title: string;
  created_at: string;
  updated_at: string;
};

export type ConversationDetail = Conversation & {
  messages: ChatMessage[];
  pending_quote: ReturnQuoteCard | null;
};

export type VoiceConfig = {
  stt: "deepgram" | "groq" | "browser";
  tts: "cartesia" | "browser";
  max_seconds: number;
  decision_model: string;
  notice: string;
};

export type ConfirmCheck = { decision: "yes" | "no" | "unclear"; reason: string; say: string };

export type AssistantStatus = {
  model: string;
  simulated: boolean;
  reason: string | null;
  prompt_versions: Record<string, string>;
  decision_model: string;
  debug: boolean;
};

export type StreamEvent =
  | { event: "signals"; data: TurnSignals }
  | { event: "status"; data: { tool: string; label: string } }
  | { event: "text"; data: { delta: string } }
  | { event: "card"; data: Card }
  | { event: "quote"; data: ReturnQuoteCard }
  | { event: "citations"; data: { valid: CitationCard[]; invalid: string[] } }
  | { event: "done"; data: { model: string; simulated: boolean; prompt_version: string } }
  | { event: "error"; data: { message: string } };
