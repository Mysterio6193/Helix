"use client";

import { useState } from "react";
import useSWR from "swr";
import { motion } from "framer-motion";
import {
  Activity,
  Chrome,
  Clock,
  Globe,
  MousePointer,
  Play,
  Plus,
  RotateCw,
  Camera,
  Square,
  Terminal,
  Trash2,
  Type,
  X,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

const ACTION_ICONS: Record<string, React.ComponentType<any>> = {
  navigate: Globe,
  click: MousePointer,
  type: Type,
                  screenshot: Camera,
  scroll: Activity,
  execute: Terminal,
};

export default function BrowserConsolePage() {
  const [newSessionUrl, setNewSessionUrl] = useState("");
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [actionInput, setActionInput] = useState("");
  const [executing, setExecuting] = useState(false);

  const { data: sessions, mutate: mutateSessions } = useSWR(
    "browser-sessions",
    () => api.browser.sessions(),
    { refreshInterval: 5000 }
  );

  const { data: automations, mutate: mutateAutomations } = useSWR(
    "browser-automations",
    () => api.browser.automations(),
    { refreshInterval: 10000 }
  );

  const { data: templates } = useSWR(
    "browser-templates",
    () => api.browser.templates(),
    { refreshInterval: 60000 }
  );
  const { data: browserStatus } = useSWR(
    "browser-status",
    () => api.get("/api/v1/browser/status"),
    { refreshInterval: 15000 }
  );

  const [replayData, setReplayData] = useState<any>(null);
  const [showReplay, setShowReplay] = useState<string | null>(null);

  const { data: sessionDetail } = useSWR(
    activeSession ? ["browser-session", activeSession] : null,
    () => api.browser.session(activeSession!),
    { refreshInterval: 3000 }
  );

  async function createSession() {
    if (!newSessionUrl) return;
    try {
      await api.browser.createSession({
        name: `Session ${new Date().toLocaleTimeString()}`,
        target_url: newSessionUrl,
      });
      setNewSessionUrl("");
      mutateSessions();
    } catch (e) {
      console.error(e);
    }
  }

  async function executeAction(actionType: string, extra: any = {}) {
    if (!activeSession) return;
    setExecuting(true);
    try {
      await api.browser.executeAction(activeSession, {
        action_type: actionType,
        ...extra,
      });
      mutateSessions();
    } catch (e) {
      console.error(e);
    } finally {
      setExecuting(false);
    }
  }

  async function runAutomation(automationId: string) {
    try {
      await api.browser.runAutomation(automationId);
      mutateAutomations();
    } catch (e) {
      console.error(e);
    }
  }

  async function loadReplay(automationId: string) {
    try {
      const data = await api.browser.replay(automationId);
      setReplayData(data);
      setShowReplay(automationId);
    } catch (e) {
      console.error(e);
    }
  }

  async function closeSession(sessionId: string) {
    try {
      await api.browser.closeSession(sessionId);
      if (activeSession === sessionId) setActiveSession(null);
      mutateSessions();
    } catch (e) {
      console.error(e);
    }
  }

  return (
    <div className="space-y-8 animate-fade-up">
      <header>
        <div className="text-eyebrow text-[color:var(--color-stone)]">
          Automation
        </div>
        <h1 className="mt-2 text-display-lg font-bold leading-tight text-white">
          Browser Console
        </h1>
        <p className="mt-3 max-w-[72ch] text-body-md text-[color:var(--color-slate)]">
          Remote browser automation for Meta Ads, Shopify, Canva, and any web
          application. Execute actions, capture evidence, and replay sessions.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_0.4fr]">
        <div className="space-y-6">
          <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
            <div className="mb-5">
              <div className="text-eyebrow text-[color:var(--color-stone)]">
                Sessions
              </div>
              <h2 className="mt-1 text-heading-lg text-white">Active Browsers</h2>
            </div>

            <div className="flex gap-2 mb-4">
              <Input
                placeholder="Enter URL to open..."
                value={newSessionUrl}
                onChange={(e) => setNewSessionUrl(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && createSession()}
              />
              <Button
                variant="primary"
                size="md"
                onClick={createSession}
                disabled={!newSessionUrl}
              >
                <Plus className="size-4" />
                Open
              </Button>
            </div>

            <div className="grid grid-cols-1 gap-3">
              {sessions?.map((session: any) => (
                <motion.div
                  key={session.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className={`rounded-lg border p-4 cursor-pointer transition-colors ${
                    activeSession === session.id
                      ? "border-white/20 bg-white/5"
                      : "border-white/[0.06] bg-black/20 hover:bg-white/[0.02]"
                  }`}
                  onClick={() => setActiveSession(session.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Chrome className="size-5 text-[color:var(--color-slate)]" />
                      <div>
                        <h3 className="text-sm font-bold text-white">
                          {session.name}
                        </h3>
                        <p className="text-[10px] text-[color:var(--color-stone)] truncate max-w-[300px]">
                          {session.current_url || session.target_url || "No URL"}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        tone={
                          session.status === "running"
                            ? "success"
                            : session.status === "error"
                            ? "error"
                            : "neutral"
                        }
                      >
                        {session.status}
                      </Badge>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          closeSession(session.id);
                        }}
                        className="p-1 rounded hover:bg-white/10 text-[color:var(--color-stone)]"
                      >
                        <Trash2 className="size-3.5" />
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))}

              {!sessions?.length && (
                <div className="text-center py-8">
                  <Chrome className="mx-auto size-8 text-[color:var(--color-stone)]" />
                  <p className="mt-3 text-sm text-[color:var(--color-slate)]">
                    No active browser sessions. Enter a URL above to start.
                  </p>
                </div>
              )}
            </div>
          </Card>

          {activeSession && sessionDetail && (
            <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <div className="text-eyebrow text-[color:var(--color-stone)]">
                    Session
                  </div>
                  <h2 className="mt-1 text-heading-lg text-white">
                    {sessionDetail.name}
                  </h2>
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setActiveSession(null)}
                >
                  <X className="size-4" />
                </Button>
              </div>

              <div className="flex flex-wrap gap-2 mb-4">
                {[
                  { type: "navigate", label: "Navigate", icon: Globe },
                  { type: "click", label: "Click", icon: MousePointer },
                  { type: "type", label: "Type", icon: Type },
                  { type: "screenshot", label: "Screenshot", icon: Camera },
                  { type: "scroll", label: "Scroll", icon: Activity },
                  { type: "execute", label: "Execute", icon: Terminal },
                ].map((action) => (
                  <button
                    key={action.type}
                    onClick={() => executeAction(action.type, { value: actionInput })}
                    disabled={executing}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-white/[0.06] bg-black/20 px-3 py-2 text-xs font-bold text-white transition hover:bg-white/[0.05] disabled:opacity-50"
                  >
                    <action.icon className="size-3.5" />
                    {action.label}
                  </button>
                ))}
              </div>

              <Input
                placeholder="Enter selector, URL, or instruction..."
                value={actionInput}
                onChange={(e) => setActionInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && executeAction("execute", { value: actionInput })}
                className="mb-4"
              />

              <div className="space-y-2">
                <h3 className="text-xs font-bold text-[color:var(--color-stone)]">
                  Action History
                </h3>
                {(sessionDetail.actions || []).length > 0 ? (
                  <div className="space-y-2 max-h-[300px] overflow-y-auto">
                    {sessionDetail.actions.map((action: any, i: number) => {
                      const Icon = ACTION_ICONS[action.action_type] || Terminal;
                      return (
                        <motion.div
                          key={action.id}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.03 }}
                          className={`rounded-lg border p-3 ${
                            action.status === "success"
                              ? "border-emerald-500/20 bg-emerald-500/5"
                              : action.status === "failed"
                              ? "border-rose-500/20 bg-rose-500/5"
                              : "border-white/[0.06] bg-black/20"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <Icon className="size-3.5 text-[color:var(--color-stone)]" />
                            <span className="text-xs font-bold text-white capitalize">
                              {action.action_type}
                            </span>
                            <Badge
                              tone={
                                action.status === "success"
                                  ? "success"
                                  : action.status === "failed"
                                  ? "error"
                                  : "neutral"
                              }
                              className="text-[8px]"
                            >
                              {action.status}
                            </Badge>
                            {action.execution_time_ms && (
                              <span className="text-[10px] text-[color:var(--color-stone)]">
                                {action.execution_time_ms}ms
                              </span>
                            )}
                          </div>
                          {action.error && (
                            <p className="mt-1 text-[10px] text-rose-300">
                              {action.error}
                            </p>
                          )}
                        </motion.div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-sm text-[color:var(--color-slate)]">
                    No actions executed yet.
                  </p>
                )}
              </div>
            </Card>
          )}

          <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
            <div className="mb-5">
              <div className="text-eyebrow text-[color:var(--color-stone)]">
                Automations
              </div>
              <h2 className="mt-1 text-heading-lg text-white">
                Saved Workflows
              </h2>
            </div>

            <div className="space-y-3">
              {automations?.map((automation: any) => (
                <div
                  key={automation.id}
                  className="rounded-lg border border-white/[0.06] bg-black/20 p-4"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Globe className="size-4 text-[color:var(--color-slate)]" />
                      <div>
                        <h3 className="text-sm font-bold text-white">
                          {automation.name}
                        </h3>
                        <p className="text-[10px] text-[color:var(--color-stone)]">
                          {automation.target_site} · {automation.action}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge tone={automation.enabled ? "success" : "neutral"}>
                        {automation.enabled ? "Active" : "Paused"}
                      </Badge>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => loadReplay(automation.id)}
                        disabled={!automation.last_run_id}
                      >
                        <RotateCw className="size-3" />
                      </Button>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => runAutomation(automation.id)}
                      >
                        <Play className="size-3" />
                      </Button>
                    </div>
                  </div>
                  <div className="mt-2 flex items-center gap-4 text-[10px] text-[color:var(--color-stone)]">
                    <span>Runs: {automation.run_count}</span>
                    <span>Success: {automation.success_count}</span>
                    {automation.last_run_at && (
                      <span>
                        Last: {new Date(automation.last_run_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
              ))}

              {!automations?.length && (
                <p className="text-center text-sm text-[color:var(--color-slate)] py-8">
                  No saved automations yet. Create one from a template below.
                </p>
              )}
            </div>
          </Card>

          {showReplay && replayData && (
            <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <div className="text-eyebrow text-[color:var(--color-stone)]">
                    Replay
                  </div>
                  <h2 className="mt-1 text-heading-lg text-white">
                    {replayData.automation_name}
                  </h2>
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setShowReplay(null)}
                >
                  <X className="size-4" />
                </Button>
              </div>

              {replayData.status === "no_runs" ? (
                <p className="text-sm text-[color:var(--color-slate)]">
                  {replayData.message}
                </p>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center gap-4 text-xs text-[color:var(--color-stone)]">
                    <span>Status: <Badge tone={replayData.status === "idle" ? "success" : replayData.status === "error" ? "error" : "neutral"}>{replayData.status}</Badge></span>
                    <span>Actions: {replayData.total_actions}</span>
                    <span>Success: {replayData.success_count}</span>
                    <span>Failed: {replayData.failed_count}</span>
                  </div>

                  <div className="space-y-2 max-h-[400px] overflow-y-auto">
                    {replayData.actions?.map((action: any, i: number) => {
                      const Icon = ACTION_ICONS[action.action_type] || Terminal;
                      return (
                        <motion.div
                          key={action.id}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.05 }}
                          className={`rounded-lg border p-3 ${
                            action.status === "success"
                              ? "border-emerald-500/20 bg-emerald-500/5"
                              : action.status === "failed"
                              ? "border-rose-500/20 bg-rose-500/5"
                              : "border-white/[0.06] bg-black/20"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <Icon className="size-3.5 text-[color:var(--color-stone)]" />
                            <span className="text-xs font-bold text-white capitalize">
                              {action.action_type}
                            </span>
                            <Badge
                              tone={
                                action.status === "success"
                                  ? "success"
                                  : action.status === "failed"
                                  ? "error"
                                  : "neutral"
                              }
                              className="text-[8px]"
                            >
                              {action.status}
                            </Badge>
                            {action.execution_time_ms && (
                              <span className="text-[10px] text-[color:var(--color-stone)]">
                                {action.execution_time_ms}ms
                              </span>
                            )}
                          </div>
                          {action.url && (
                            <p className="mt-1 text-[10px] text-[color:var(--color-stone)] truncate">
                              {action.url}
                            </p>
                          )}
                          {action.error && (
                            <p className="mt-1 text-[10px] text-rose-300">
                              {action.error}
                            </p>
                          )}
                          {action.result && Object.keys(action.result).length > 0 && (
                            <pre className="mt-1 text-[9px] text-[color:var(--color-stone)] overflow-x-auto">
                              {JSON.stringify(action.result, null, 2)}
                            </pre>
                          )}
                        </motion.div>
                      );
                    })}
                  </div>
                </div>
              )}
            </Card>
          )}
        </div>

        <div className="space-y-6">
          <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
            <div className="mb-4">
              <div className="text-eyebrow text-[color:var(--color-stone)]">
                Templates
              </div>
              <h2 className="mt-1 text-heading-lg text-white">Quick Start</h2>
            </div>

            <div className="space-y-3">
              {templates?.map((template: any) => (
                <div
                  key={template.id}
                  className="rounded-lg border border-white/[0.06] bg-black/20 p-3 hover:bg-white/[0.02] transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <Globe className="size-4 text-[color:var(--color-slate)]" />
                    <span className="text-xs font-bold text-white">
                      {template.name}
                    </span>
                  </div>
                  <p className="mt-1 text-[10px] text-[color:var(--color-stone)]">
                    {template.description}
                  </p>
                </div>
              ))}
            </div>
          </Card>

          <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
            <div className="mb-4">
              <div className="text-eyebrow text-[color:var(--color-stone)]">
                Status
              </div>
              <h2 className="mt-1 text-heading-lg text-white">System</h2>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-[color:var(--color-slate)]">Browser Engine</span>
                <div className="flex items-center gap-1.5">
                  <div className="size-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-xs text-emerald-400">Active</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-[color:var(--color-slate)]">Active Sessions</span>
                <Badge tone="info">{sessions?.length || 0}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-[color:var(--color-slate)]">Automations</span>
                <Badge tone="info">{automations?.length || 0}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-[color:var(--color-slate)]">Provider</span>
                <span className="text-xs text-white">
                  {browserStatus?.available ? "Playwright" : "Simulated"}
                  {browserStatus?.connected ? " (connected)" : ""}
                </span>
              </div>
              <div className="pt-2 border-t border-white/[0.06]">
                <Button
                  variant="secondary"
                  size="sm"
                  className="w-full"
                  onClick={async () => {
                    try {
                      const result = await api.browser.testTrigger(
                        "Creative Fatigue Detected",
                        "CTR declined 30% over 3 days"
                      );
                      alert(`Trigger test: ${result.triggered} automation(s) fired`);
                    } catch (e) {
                      console.error(e);
                    }
                  }}
                >
                  <Activity className="size-3 mr-1" />
                  Test Trigger
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
