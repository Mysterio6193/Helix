import { NextResponse } from "next/server";

/**
 * Contact form intake.
 *
 * Persists submissions to a local JSONL file under `apps/web/.data/contact.jsonl`
 * so operators can review inquiries without standing up an external service.
 *
 * If an outbound SMTP / email forwarder is configured via env later, this
 * handler can be extended to deliver the payload there too.
 */

import fs from "node:fs/promises";
import path from "node:path";

interface ContactPayload {
  name?: string;
  email?: string;
  company?: string;
  topic?: string;
  message?: string;
  source?: string;
}

const MAX_BODY = 8_000;

function isValidEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}

export async function POST(req: Request) {
  let body: ContactPayload;
  try {
    body = (await req.json()) as ContactPayload;
  } catch {
    return NextResponse.json(
      { ok: false, error: "Invalid JSON body" },
      { status: 400 },
    );
  }

  const name = (body.name ?? "").trim();
  const email = (body.email ?? "").trim();
  const company = (body.company ?? "").trim();
  const topic = (body.topic ?? "").trim();
  const message = (body.message ?? "").trim();

  if (!name || name.length > 200) {
    return NextResponse.json(
      { ok: false, error: "Name is required (max 200 chars)" },
      { status: 400 },
    );
  }
  if (!isValidEmail(email)) {
    return NextResponse.json(
      { ok: false, error: "A valid email is required" },
      { status: 400 },
    );
  }
  if (!message || message.length < 10) {
    return NextResponse.json(
      { ok: false, error: "Message must be at least 10 characters" },
      { status: 400 },
    );
  }
  if (message.length > MAX_BODY) {
    return NextResponse.json(
      { ok: false, error: `Message must be under ${MAX_BODY} characters` },
      { status: 400 },
    );
  }

  const record = {
    id: crypto.randomUUID(),
    received_at: new Date().toISOString(),
    name,
    email,
    company: company || null,
    topic: topic || null,
    message,
    source: body.source ?? "contact-page",
    ip:
      req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? null,
    user_agent: req.headers.get("user-agent") ?? null,
  };

  try {
    const dir = path.join(process.cwd(), ".data");
    await fs.mkdir(dir, { recursive: true });
    await fs.appendFile(
      path.join(dir, "contact.jsonl"),
      JSON.stringify(record) + "\n",
      "utf8",
    );
  } catch (err) {
    console.error("[contact] failed to persist submission", err);
    // We still return success to the client; admins can recover from logs.
  }

  // Mirror to server logs so operators see inquiries in real time.
  console.log(
    `[contact] ${record.id} from ${name} <${email}>${
      company ? ` (${company})` : ""
    }${topic ? ` · ${topic}` : ""}`,
  );

  return NextResponse.json({ ok: true, id: record.id });
}

export async function GET() {
  return NextResponse.json(
    { ok: false, error: "Use POST to submit a contact inquiry" },
    { status: 405 },
  );
}
