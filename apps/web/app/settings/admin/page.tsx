"use client";

import { useCallback, useState } from "react";
import useSWR from "swr";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";

function roleBadgeTone(role: string): "success" | "warning" | "info" | "neutral" {
  switch (role) {
    case "owner": return "success";
    case "admin": return "warning";
    case "member": return "info";
    default: return "neutral";
  }
}

export default function AdminSettingsPage() {
  const { data: auth } = useSWR("auth-me", () => api.auth.me());
  const { data: members, mutate: refreshMembers } = useSWR(
    auth?.authenticated ? "org-members" : null,
    () => api.enterprise.members(),
  );
  const { data: invitations, mutate: refreshInvites } = useSWR(
    auth?.authenticated ? "org-invitations" : null,
    () => api.enterprise.invitations(),
  );
  const { data: usage } = useSWR(
    auth?.authenticated ? "org-usage" : null,
    () => api.enterprise.usage(),
  );

  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [inviting, setInviting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleInvite = useCallback(async () => {
    if (!inviteEmail) return;
    setErrorMsg(null);
    setSuccessMsg(null);
    setInviting(true);
    try {
      await api.enterprise.createInvitation({ email: inviteEmail, role: inviteRole });
      setSuccessMsg(`Invitation sent to ${inviteEmail}`);
      setInviteEmail("");
      refreshInvites();
      refreshMembers();
    } catch (err) {
      setErrorMsg(err instanceof ApiError ? err.message : String(err));
    } finally {
      setInviting(false);
    }
  }, [inviteEmail, inviteRole, refreshInvites, refreshMembers]);

  const handleChangeRole = useCallback(async (memberId: string, role: string) => {
    try {
      await api.enterprise.updateMemberRole(memberId, { role });
      refreshMembers();
    } catch (err) {
      setErrorMsg(err instanceof ApiError ? err.message : String(err));
    }
  }, [refreshMembers]);

  const handleRemoveMember = useCallback(async (memberId: string) => {
    if (!confirm("Remove this member from the organization?")) return;
    try {
      await api.enterprise.removeMember(memberId);
      refreshMembers();
    } catch (err) {
      setErrorMsg(err instanceof ApiError ? err.message : String(err));
    }
  }, [refreshMembers]);

  const handleRevokeInvite = useCallback(async (id: string) => {
    try {
      await api.enterprise.revokeInvitation(id);
      refreshInvites();
    } catch (err) {
      setErrorMsg(err instanceof ApiError ? err.message : String(err));
    }
  }, [refreshInvites]);

  if (!auth?.authenticated) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16">
        <h1 className="mb-3 text-2xl font-semibold">Admin</h1>
        <p className="text-muted-foreground">Please sign in to manage your organization.</p>
      </div>
    );
  }

  const isAdmin = auth.user?.role === "owner" || auth.user?.role === "admin";

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight">Admin</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage your organization, team members, and invitations.
        </p>
      </div>

      {errorMsg ? (
        <div className="mb-6 rounded-md border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-700">{errorMsg}</div>
      ) : null}
      {successMsg ? (
        <div className="mb-6 rounded-md border border-green-500/40 bg-green-500/10 p-3 text-sm text-green-700">{successMsg}</div>
      ) : null}

      {/* Usage */}
      {usage ? (
        <Card className="mb-6 p-4">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">Usage</h2>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div>
              <div className="text-xs text-muted-foreground">Brands</div>
              <div className="text-lg font-semibold">{usage.brands} / {usage.brand_limit ?? "∞"}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Runs / month</div>
              <div className="text-lg font-semibold">{usage.runs_this_month} / {usage.run_limit ?? "∞"}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Members</div>
              <div className="text-lg font-semibold">{usage.members} / {usage.member_limit ?? "∞"}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">API Keys</div>
              <div className="text-lg font-semibold">{usage.api_keys} / {usage.api_key_limit}</div>
            </div>
          </div>
        </Card>
      ) : null}

      {/* Members */}
      <Card className="mb-6 p-4">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Team Members</h2>
        </div>
        {!members || members.length === 0 ? (
          <p className="text-sm text-muted-foreground">No members found.</p>
        ) : (
          <div className="space-y-3">
            {members.map((m) => (
              <div key={m.id} className="flex items-center justify-between rounded-lg border p-3">
                <div>
                  <div className="text-sm font-medium">{m.name || m.email}</div>
                  <div className="text-xs text-muted-foreground">{m.email}</div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge tone={roleBadgeTone(m.role)}>{m.role}</Badge>
                  {isAdmin && m.role !== "owner" && (
                    <div className="flex gap-1">
                      <select
                        value={m.role}
                        onChange={(e) => handleChangeRole(m.id, e.target.value)}
                        className="rounded border bg-transparent px-2 py-1 text-xs"
                      >
                        <option value="member">member</option>
                        <option value="admin">admin</option>
                      </select>
                      <button
                        onClick={() => handleRemoveMember(m.id)}
                        className="rounded px-2 py-1 text-xs text-red-500 hover:bg-red-500/10"
                      >
                        Remove
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Invitations */}
      {isAdmin ? (
        <Card className="mb-6 p-4">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">Invite People</h2>
          <div className="mb-4 flex gap-2">
            <Input
              type="email"
              placeholder="colleague@example.com"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              className="flex-1"
            />
            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
              className="rounded border bg-transparent px-2 py-1 text-sm"
            >
              <option value="member">Member</option>
              <option value="admin">Admin</option>
            </select>
            <Button onClick={handleInvite} disabled={inviting || !inviteEmail} variant="primary">
              {inviting ? "Sending…" : "Send Invite"}
            </Button>
          </div>

          {invitations && invitations.length > 0 ? (
            <div>
              <h3 className="mb-2 text-xs uppercase tracking-wide text-muted-foreground">Pending Invitations</h3>
              <div className="space-y-2">
                {invitations.map((inv) => (
                  <div key={inv.id} className="flex items-center justify-between rounded-lg border p-3">
                    <div>
                      <div className="text-sm">{inv.email}</div>
                      <div className="text-xs text-muted-foreground">
                        Role: {inv.role} &middot; Expires {new Date(inv.expires_at).toLocaleDateString()}
                      </div>
                    </div>
                    <button
                      onClick={() => handleRevokeInvite(inv.id)}
                      className="rounded px-2 py-1 text-xs text-red-500 hover:bg-red-500/10"
                    >
                      Revoke
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </Card>
      ) : null}
    </div>
  );
}
