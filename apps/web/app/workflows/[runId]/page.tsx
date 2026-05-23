"use client";

import Link from "next/link";
import { use } from "react";
import useSWR from "swr";

import { Badge, statusTone } from "@/components/ui/badge";
import { Card, CardSubtitle, CardTitle } from "@/components/ui/card";
import { AgentTimeline } from "@/components/workflow/agent-timeline";
import { GraphViz } from "@/components/workflow/graph-viz";
import { RunStream } from "@/components/workflow/run-stream";
import { api, type RunDetail } from "@/lib/api";
import { formatRelative, shortId } from "@/lib/utils";

interface PageProps {
  params: Promise<{ runId: string }>;
}

export default function RunDetailPage({ params }: PageProps) {
  const { runId } = use(params);
  const { data: run, error, isLoading } = useSWR<RunDetail>(
    ["run", runId],
    () => api.runs.get(runId),
    { refreshInterval: 3000 },
  );

  return (
    <div className="space-y-8">
      <header className="flex items-start justify-between gap-6">
        <div>
          <div className="text-eyebrow text-[color:var(--color-stone)]">
            <Link href="/workflows" className="hover:underline">
              Workflows
            </Link>{" "}
            · {shortId(runId)}
          </div>
          {isLoading && (
            <h1 className="text-display-lg text-[color:var(--color-muted)]">
              Loading…
            </h1>
          )}
          {error && (
            <h1 className="text-display-lg text-[color:var(--color-error-text)]">
              Not found
            </h1>
          )}
          {run && (
            <>
              <h1 className="text-display-lg text-[color:var(--color-charcoal)]">
                {run.workflow}
              </h1>
              <p className="mt-2 text-body-sm text-[color:var(--color-stone)] tabular">
                created {formatRelative(run.created_at)} · brand {shortId(run.brand_id)}
              </p>
            </>
          )}
        </div>
        {run && (
          <Badge tone={statusTone(run.status)} className="text-label">
            {run.status}
          </Badge>
        )}
      </header>

      {run && (
        <GraphViz runId={runId} workflowSlice={run.workflow} />
      )}

      {!!run?.state?.steps && (run.state.steps as any[]).length > 0 && (
        <AgentTimeline run={run} />
      )}

      <RunStream runId={runId} />

      {run?.output && Object.keys(run.output).length > 0 && (
        <Card feature>
          <CardTitle>Output</CardTitle>
          <CardSubtitle>Final state slice produced by the graph.</CardSubtitle>
          <pre className="mt-4 max-h-[480px] overflow-auto rounded-[12px] bg-[color:var(--color-canvas)] border border-[color:var(--color-hairline)] p-4 text-body-sm text-[color:var(--color-slate)] tabular">
            {JSON.stringify(run.output, null, 2)}
          </pre>
        </Card>
      )}

      {run?.error && (
        <Card>
          <CardTitle>Error</CardTitle>
          <pre className="mt-4 rounded-[12px] bg-[color:var(--color-error-bg)] border border-[color:var(--color-hairline)] p-4 text-body-sm text-[color:var(--color-error-text)] tabular whitespace-pre-wrap">
            {String(run.error)}
          </pre>
        </Card>
      )}
    </div>
  );
}
