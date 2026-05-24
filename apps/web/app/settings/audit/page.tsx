"use client";

import { useState } from "react";
import useSWR from "swr";

import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

const ACTION_LABELS: Record<string, string> = {
  "api_key.create": "API Key Created",
  "api_key.delete": "API Key Revoked",
  "member.role_update": "Member Role Changed",
  "member.remove": "Member Removed",
  "invitation.create": "Invitation Sent",
  "invitation.revoke": "Invitation Revoked",
};

const RESOURCE_LABELS: Record<string, string> = {
  api_key: "API Key",
  user: "User",
  invitation: "Invitation",
  brand: "Brand",
  workspace: "Workspace",
};

export default function AuditLogPage() {
  const { data: auth } = useSWR("auth-me", () => api.auth.me());
  const [actionFilter, setActionFilter] = useState("");
  const [offset, setOffset] = useState(0);
  const limit = 50;

  const qs = new URLSearchParams();
  if (actionFilter) qs.set("action", actionFilter);
  qs.set("offset", String(offset));
  qs.set("limit", String(limit));

  const { data, isLoading, mutate } = useSWR(
    auth?.authenticated ? `audit-logs-${qs.toString()}` : null,
    () => api.enterprise.auditLogs({
      action: actionFilter || undefined,
      offset,
      limit,
    }),
  );

  if (!auth?.authenticated) {
    return (
      <div className="mx-auto max-w-4xl px-6 py-16">
        <h1 className="mb-3 text-2xl font-semibold">Audit Log</h1>
        <p className="text-muted-foreground">Please sign in to view audit logs.</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight">Audit Log</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Track changes made across your organization.
        </p>
      </div>

      {/* Filters */}
      <Card className="mb-6 p-4">
        <div className="flex flex-wrap gap-3">
          <div className="flex-1">
            <label className="mb-1 block text-xs text-muted-foreground">Action</label>
            <select
              value={actionFilter}
              onChange={(e) => { setActionFilter(e.target.value); setOffset(0); }}
              className="w-full rounded border bg-transparent px-3 py-2 text-sm"
            >
              <option value="">All actions</option>
              {Object.entries(ACTION_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {/* Log entries */}
      <Card className="p-4">
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded bg-muted" />
            ))}
          </div>
        ) : !data || data.items.length === 0 ? (
          <p className="text-sm text-muted-foreground">No audit log entries found.</p>
        ) : (
          <>
            <div className="space-y-2">
              {data.items.map((entry) => {
                const label = ACTION_LABELS[entry.action] || entry.action;
                const resourceLabel = RESOURCE_LABELS[entry.resource_type] || entry.resource_type;
                return (
                  <div key={entry.id} className="rounded-lg border p-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="text-sm font-medium">{label}</div>
                        <div className="text-xs text-muted-foreground">
                          {resourceLabel}
                          {entry.resource_id ? ` · ${entry.resource_id.slice(0, 8)}...` : ""}
                        </div>
                      </div>
                      <div className="text-right text-xs text-muted-foreground">
                        {new Date(entry.created_at).toLocaleString()}
                      </div>
                    </div>
                    {Object.keys(entry.details || {}).length > 0 && (
                      <pre className="mt-2 overflow-x-auto rounded bg-muted p-2 text-xs">
                        {JSON.stringify(entry.details, null, 2)}
                      </pre>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Pagination */}
            <div className="mt-4 flex items-center justify-between border-t pt-4">
              <button
                onClick={() => setOffset(Math.max(0, offset - limit))}
                disabled={offset === 0}
                className="rounded px-3 py-1 text-sm hover:bg-muted disabled:opacity-30"
              >
                Previous
              </button>
              <span className="text-xs text-muted-foreground">
                {offset + 1}–{Math.min(offset + limit, data.total)} of {data.total}
              </span>
              <button
                onClick={() => setOffset(offset + limit)}
                disabled={offset + limit >= data.total}
                className="rounded px-3 py-1 text-sm hover:bg-muted disabled:opacity-30"
              >
                Next
              </button>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
