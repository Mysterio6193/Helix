"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ArrowUp, Loader2, RefreshCw, Sparkles, Square, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ModelPicker } from "@/components/model-picker";
import {
  formatCost,
  llmApi,
  modelPriceLabel,
  useModelCatalog,
  useWorkspacePrefs,
  type ModelEntry,
} from "@/lib/llm";
import { cn } from "@/lib/utils";

type Role = "system" | "user" | "assistant";

interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  model?: string;
  provider?: string;
  cost_usd?: number | null;
  prompt_tokens?: number | null;
  completion_tokens?: number | null;
  pending?: boolean;
}

const STORAGE_KEY = "helix:chat:v1";
const SYSTEM_PROMPT =
  "You are Helix, the AI creative OS. Be concise, concrete, and helpful. " +
  "If the user asks for marketing copy, brand work, or design, ask for the brand/audience if missing.";

function uid(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function loadHistory(): ChatMessage[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed as ChatMessage[];
  } catch {
    return [];
  }
}

function saveHistory(messages: ChatMessage[]): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  } catch {
    // ignore quota errors
  }
}

export default function ChatPage() {
  const { data: catalog } = useModelCatalog("chat");
  const { data: prefs } = useWorkspacePrefs();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [model, setModel] = useState<string | null>(null);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  // hydrate from local storage
  useEffect(() => {
    setMessages(loadHistory());
  }, []);

  // sync model default from preferences
  useEffect(() => {
    if (model || !prefs?.default_chat_model) return;
    setModel(prefs.default_chat_model);
  }, [model, prefs]);

  // persist conversation
  useEffect(() => {
    saveHistory(messages);
  }, [messages]);

  // scroll to bottom on new messages
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  // auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 200)}px`;
  }, [input]);

  const selectedModel = useMemo<ModelEntry | undefined>(
    () => catalog?.models.find((m) => m.id === model),
    [catalog, model],
  );

  const supportsStreaming = selectedModel?.supports_streaming ?? false;
  const modelUnavailable = selectedModel ? !selectedModel.available : false;

  const totalCost = useMemo(
    () =>
      messages.reduce((sum, m) => sum + (m.cost_usd ?? 0), 0),
    [messages],
  );

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || streaming) return;
    setError(null);

    const userMsg: ChatMessage = { id: uid(), role: "user", content: text };
    const placeholder: ChatMessage = {
      id: uid(),
      role: "assistant",
      content: "",
      model: model ?? undefined,
      pending: true,
    };
    const nextHistory = [...messages, userMsg, placeholder];
    setMessages(nextHistory);
    setInput("");
    setStreaming(true);

    const ctrl = new AbortController();
    abortRef.current = ctrl;

    // Build provider-format messages (exclude pending placeholder)
    const apiMessages = [
      ...messages,
      userMsg,
    ]
      .filter((m) => !m.pending && m.content)
      .map((m) => ({ role: m.role, content: m.content }));

    try {
      if (supportsStreaming) {
        let acc = "";
        for await (const chunk of llmApi.stream({
          model: model ?? undefined,
          messages: apiMessages,
          system: SYSTEM_PROMPT,
          temperature: 0.7,
          max_tokens: 1500,
        }, ctrl.signal)) {
          acc += chunk;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === placeholder.id ? { ...m, content: acc } : m,
            ),
          );
        }
        // Stream done — finalize. (cost/tokens not exposed via SSE in this gateway)
        setMessages((prev) =>
          prev.map((m) =>
            m.id === placeholder.id
              ? {
                  ...m,
                  content: acc,
                  pending: false,
                  model: model ?? m.model,
                  provider: selectedModel?.provider,
                }
              : m,
          ),
        );
      } else {
        const result = await llmApi.complete({
          model: model ?? undefined,
          messages: apiMessages,
          system: SYSTEM_PROMPT,
          temperature: 0.7,
          max_tokens: 1500,
        });
        setMessages((prev) =>
          prev.map((m) =>
            m.id === placeholder.id
              ? {
                  ...m,
                  content: result.text,
                  model: result.model,
                  provider: result.provider,
                  prompt_tokens: result.prompt_tokens,
                  completion_tokens: result.completion_tokens,
                  cost_usd: result.cost_usd,
                  pending: false,
                }
              : m,
          ),
        );
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      if (msg !== "aborted") {
        setError(msg);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === placeholder.id
              ? { ...m, content: `[error] ${msg}`, pending: false }
              : m,
          ),
        );
      } else {
        setMessages((prev) => prev.filter((m) => m.id !== placeholder.id));
      }
    } finally {
      setStreaming(false);
      abortRef.current = null;
    }
  }, [input, streaming, messages, model, supportsStreaming, selectedModel]);

  const stop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const clear = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col gap-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles size={20} className="text-[color:var(--color-ink)]" />
            <h1 className="text-heading-lg">Chat</h1>
          </div>
          <p className="text-body-sm text-[color:var(--color-slate)]">
            Talk to any model in the Helix catalog. Server holds the keys.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ModelPicker
            capability="chat"
            value={model}
            onChange={setModel}
            label="Model"
            compact
            className="min-w-[280px]"
          />
          <Button
            variant="secondary"
            size="sm"
            onClick={clear}
            disabled={messages.length === 0 || streaming}
            aria-label="Clear conversation"
          >
            <Trash2 size={14} />
            Clear
          </Button>
        </div>
      </header>

      <Card className="flex flex-1 min-h-0 flex-col overflow-hidden">
        <div className="flex flex-1 min-h-0 flex-col">
          <div className="flex-1 overflow-y-auto px-6 py-6">
            {messages.length === 0 ? (
              <EmptyState model={selectedModel} />
            ) : (
              <div className="mx-auto flex max-w-3xl flex-col gap-6">
                {messages.map((m) => (
                  <MessageBubble key={m.id} message={m} />
                ))}
                <div ref={endRef} />
              </div>
            )}
          </div>

          {modelUnavailable && (
            <div className="border-t border-[color:var(--color-hairline)] bg-[color:var(--color-surface)] px-6 py-2 text-body-sm text-[color:var(--color-stone)]">
              {selectedModel?.display_name} has no server-side key configured. Add{" "}
              <code className="rounded bg-[color:var(--color-surface-elev)] px-1.5 py-0.5 text-micro">
                {settingsAttrFor(selectedModel)}
              </code>{" "}
              to <code className="rounded bg-[color:var(--color-surface-elev)] px-1.5 py-0.5 text-micro">apps/api/.env</code> to enable it.
            </div>
          )}

          {error && (
            <div className="border-t border-[color:var(--color-hairline)] bg-[color:var(--color-surface)] px-6 py-2 text-body-sm text-red-400">
              {error}
            </div>
          )}

          <div className="border-t border-[color:var(--color-hairline)] bg-[color:var(--color-canvas)] p-4">
            <div className="mx-auto flex max-w-3xl items-end gap-2">
              <div className="flex-1">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={onKeyDown}
                  placeholder={streaming ? "Streaming..." : "Message Helix..."}
                  rows={1}
                  disabled={streaming}
                  className={cn(
                    "block w-full resize-none rounded-[12px] border border-[color:var(--color-hairline)]",
                    "bg-[color:var(--color-surface)] px-4 py-3 text-body-md text-[color:var(--color-ink)]",
                    "placeholder:text-[color:var(--color-stone)]",
                    "focus-visible:outline-none focus-visible:border-[color:var(--color-ink)]",
                    "disabled:opacity-60",
                  )}
                  style={{ maxHeight: 200 }}
                />
              </div>
              {streaming ? (
                <Button
                  variant="secondary"
                  size="md"
                  onClick={stop}
                  aria-label="Stop generation"
                >
                  <Square size={14} />
                  Stop
                </Button>
              ) : (
                <Button
                  variant="primary"
                  size="md"
                  onClick={send}
                  disabled={!input.trim() || modelUnavailable}
                  aria-label="Send message"
                >
                  <ArrowUp size={14} />
                  Send
                </Button>
              )}
            </div>
            <div className="mx-auto mt-2 flex max-w-3xl items-center justify-between text-micro text-[color:var(--color-stone)]">
              <div className="flex items-center gap-2">
                {selectedModel ? (
                  <>
                    <span>{selectedModel.display_name}</span>
                    <span>·</span>
                    <span>{modelPriceLabel(selectedModel)}</span>
                    {selectedModel.supports_streaming && (
                      <>
                        <span>·</span>
                        <span>streams</span>
                      </>
                    )}
                  </>
                ) : (
                  <span>No model selected</span>
                )}
              </div>
              <div>Session cost: {formatCost(totalCost)}</div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}>
      <div className={cn("flex max-w-[85%] flex-col gap-1", isUser && "items-end")}>
        <div
          className={cn(
            "rounded-[14px] px-4 py-3 text-body-md whitespace-pre-wrap break-words",
            isUser
              ? "bg-[color:var(--color-ink)] text-[color:var(--color-canvas)]"
              : "bg-[color:var(--color-surface-elev)] text-[color:var(--color-ink)]",
          )}
        >
          {message.pending && !message.content ? (
            <span className="inline-flex items-center gap-2 text-[color:var(--color-stone)]">
              <Loader2 size={14} className="animate-spin" />
              Thinking…
            </span>
          ) : (
            message.content
          )}
        </div>
        {!isUser && !message.pending && message.content && (
          <div className="flex flex-wrap items-center gap-2 text-micro text-[color:var(--color-stone)]">
            {message.model && <span>{message.model}</span>}
            {message.completion_tokens != null && (
              <>
                <span>·</span>
                <span>
                  {message.prompt_tokens ?? 0}→{message.completion_tokens} tok
                </span>
              </>
            )}
            {message.cost_usd != null && (
              <>
                <span>·</span>
                <span>{formatCost(message.cost_usd)}</span>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function EmptyState({ model }: { model?: ModelEntry }) {
  const suggestions = [
    "Write 3 tagline options for a third-wave coffee brand.",
    "Outline a 7-day Instagram content plan for a wellness studio.",
    "Critique this brand voice: 'Bold, but kind. Direct, but warm.'",
    "Suggest 5 packaging copy lines for a cold-pressed juice.",
  ];
  return (
    <div className="mx-auto flex h-full max-w-2xl flex-col items-center justify-center gap-6 text-center">
      <div className="flex items-center gap-2">
        <RefreshCw size={28} className="text-[color:var(--color-stone)]" />
      </div>
      <div>
        <h2 className="text-heading-md">Start a conversation</h2>
        <p className="mt-2 text-body-md text-[color:var(--color-slate)]">
          You're talking to{" "}
          <span className="text-[color:var(--color-ink)]">
            {model?.display_name ?? "the default model"}
          </span>
          . Pick another from the dropdown anytime.
        </p>
      </div>
      <div className="flex flex-wrap justify-center gap-2">
        {model?.tags.slice(0, 4).map((t) => (
          <Badge key={t} tone="info">
            {t}
          </Badge>
        ))}
      </div>
      <div className="grid w-full grid-cols-1 gap-2 sm:grid-cols-2">
        {suggestions.map((s) => (
          <SuggestionTile key={s} text={s} />
        ))}
      </div>
    </div>
  );
}

function SuggestionTile({ text }: { text: string }) {
  return (
    <button
      type="button"
      onClick={() => {
        const ta = document.querySelector<HTMLTextAreaElement>("textarea");
        if (ta) {
          ta.value = text;
          ta.dispatchEvent(new Event("input", { bubbles: true }));
          ta.focus();
        }
      }}
      className={cn(
        "rounded-[12px] border border-[color:var(--color-hairline)] bg-[color:var(--color-surface)]",
        "px-4 py-3 text-left text-body-sm text-[color:var(--color-slate)]",
        "transition-colors hover:border-[color:var(--color-ink)] hover:text-[color:var(--color-ink)]",
      )}
    >
      {text}
    </button>
  );
}

function settingsAttrFor(model?: ModelEntry): string {
  if (!model) return "";
  return (
    {
      openai: "OPENAI_API_KEY",
      anthropic: "ANTHROPIC_API_KEY",
      gemini: "GEMINI_API_KEY",
      openrouter: "OPENROUTER_API_KEY",
      replicate: "REPLICATE_API_TOKEN",
      runway: "RUNWAY_API_KEY",
      veo: "GOOGLE_VEO_API_KEY",
    } as Record<string, string>
  )[model.provider] ?? "API_KEY";
}
