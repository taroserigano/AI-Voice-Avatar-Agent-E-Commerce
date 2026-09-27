import type {
  AgentName,
  AssistantStatus,
  ConfirmCheck,
  Conversation,
  ConversationDetail,
  StreamEvent,
  VoiceConfig,
} from "./assistant-types";

/** The assistant API, through the web app's /api/assistant rewrite (the session cookie rides along). */
const BASE = "/api/assistant";

export class AssistantHttpError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

async function json<T>(resp: Response): Promise<T> {
  if (!resp.ok) throw new AssistantHttpError(resp.status, `Assistant API ${resp.status}`);
  return (await resp.json()) as T;
}

export async function getStatus(): Promise<AssistantStatus> {
  return json(await fetch(`${BASE}/status`, { credentials: "same-origin" }));
}

export async function createConversation(agent: AgentName): Promise<Conversation> {
  return json(
    await fetch(`${BASE}/conversations`, {
      method: "POST",
      credentials: "same-origin",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ agent }),
    }),
  );
}

export async function getConversation(id: string): Promise<ConversationDetail> {
  return json(await fetch(`${BASE}/conversations/${encodeURIComponent(id)}`, { credentials: "same-origin" }));
}

/**
 * Split server-sent event text into complete events. Returns the events and whatever
 * trailing partial text must wait for the next chunk.
 */
export function parseSse(buffer: string): { events: StreamEvent[]; rest: string } {
  const events: StreamEvent[] = [];
  const blocks = buffer.replace(/\r\n/g, "\n").split("\n\n");
  const rest = blocks.pop() ?? "";
  for (const block of blocks) {
    let event = "message";
    const data: string[] = [];
    for (const line of block.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
    }
    if (!data.length) continue;
    try {
      events.push({ event, data: JSON.parse(data.join("\n")) } as StreamEvent);
    } catch {
      // A malformed event is skipped rather than breaking the whole answer.
    }
  }
  return { events, rest };
}

async function* streamEvents(path: string, body: unknown, signal?: AbortSignal): AsyncGenerator<StreamEvent> {
  const resp = await fetch(`${BASE}${path}`, {
    method: "POST",
    credentials: "same-origin",
    headers: { "content-type": "application/json", accept: "text/event-stream" },
    body: JSON.stringify(body),
    signal,
  });
  if (!resp.ok || !resp.body) throw new AssistantHttpError(resp.status, `Assistant API ${resp.status}`);
  const reader = resp.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += value;
    const parsed = parseSse(buffer);
    buffer = parsed.rest;
    yield* parsed.events;
  }
  if (buffer.trim()) yield* parseSse(`${buffer}\n\n`).events;
}

/** Send one message and yield the answer's events as they stream in. */
export function sendMessage(
  conversationId: string,
  text: string,
  signal?: AbortSignal,
  voice = false,
): AsyncGenerator<StreamEvent> {
  return streamEvents(`/conversations/${encodeURIComponent(conversationId)}/messages`, { text, voice }, signal);
}

/** Continue a turn paused on a quote, after the customer confirmed or declined it with the store. */
export function resumeTurn(
  conversationId: string,
  quoteId: string,
  outcome: "confirmed" | "declined",
  signal?: AbortSignal,
  voice = false,
): AsyncGenerator<StreamEvent> {
  return streamEvents(
    `/conversations/${encodeURIComponent(conversationId)}/resume`,
    { quote_id: quoteId, outcome, voice },
    signal,
  );
}

// --- Voice ------------------------------------------------------------------------------------

export async function getVoiceConfig(): Promise<VoiceConfig> {
  return json(await fetch(`${BASE}/voice/config`, { credentials: "same-origin" }));
}

/** Server speech-to-text for one recorded turn. 503 means "use the browser's recognizer". */
export async function transcribe(audio: Blob): Promise<{ text: string; provider: string; latency_ms: number }> {
  const form = new FormData();
  form.append("audio", audio, `speech.${audio.type.includes("ogg") ? "ogg" : audio.type.includes("mp4") ? "mp4" : "webm"}`);
  return json(await fetch(`${BASE}/voice/transcribe`, { method: "POST", credentials: "same-origin", body: form }));
}

/** The assistant's voice for `text` as MP3. 503 means "use the browser's voice". */
export async function speak(text: string, agent: AgentName): Promise<Blob> {
  const resp = await fetch(`${BASE}/voice/speak`, {
    method: "POST",
    credentials: "same-origin",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ text, agent }),
  });
  if (!resp.ok) throw new AssistantHttpError(resp.status, `Assistant API ${resp.status}`);
  return resp.blob();
}

export async function confirmCheck(body: {
  text: string;
  final: boolean;
  readback_complete: boolean;
  speech_ms: number;
  conversation_id: string;
  quote_id: string;
}): Promise<ConfirmCheck> {
  return json(
    await fetch(`${BASE}/voice/confirm-check`, {
      method: "POST",
      credentials: "same-origin",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    }),
  );
}
