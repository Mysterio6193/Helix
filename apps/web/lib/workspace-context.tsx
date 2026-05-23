"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import useSWR from "swr";
import { api, type Workspace } from "./api";

interface WorkspaceContextType {
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  activeWorkspaceId: string | null;
  setActiveWorkspaceId: (id: string) => void;
  isLoading: boolean;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [activeWorkspaceId, setActiveWorkspaceIdState] = useState<string | null>(null);

  const { data: workspaces = [], isLoading } = useSWR<Workspace[]>(
    "workspaces",
    () => api.workspaces.list(),
    { fallbackData: [] }
  );

  // Initialize from local storage or first workspace
  useEffect(() => {
    if (workspaces.length > 0 && !activeWorkspaceId) {
      const stored = localStorage.getItem("helix_active_workspace");
      if (stored && workspaces.some(w => w.id === stored)) {
        setActiveWorkspaceIdState(stored);
      } else {
        setActiveWorkspaceIdState(workspaces[0].id);
        localStorage.setItem("helix_active_workspace", workspaces[0].id);
      }
    }
  }, [workspaces, activeWorkspaceId]);

  const setActiveWorkspaceId = (id: string) => {
    setActiveWorkspaceIdState(id);
    localStorage.setItem("helix_active_workspace", id);
    // Ideally we might trigger an SWR cache invalidation here for workspace-dependent queries
  };

  const activeWorkspace = workspaces.find((w) => w.id === activeWorkspaceId) || (workspaces.length > 0 ? workspaces[0] : null);

  return (
    <WorkspaceContext.Provider
      value={{
        workspaces,
        activeWorkspace,
        activeWorkspaceId,
        setActiveWorkspaceId,
        isLoading,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (context === undefined) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return context;
}
