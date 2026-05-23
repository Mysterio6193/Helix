"use client";

import { useEffect, useState, useCallback } from "react";
import { Check, ChevronsUpDown, Plus, Building } from "lucide-react";
import { cn } from "@/lib/utils";
import { useWorkspace } from "@/lib/workspace-context";

export function WorkspaceSwitcher() {
  const [isOpen, setIsOpen] = useState(false);
  const { workspaces, activeWorkspace, activeWorkspaceId, setActiveWorkspaceId, isLoading } = useWorkspace();



  if (isLoading || !workspaces || workspaces.length === 0) {
    return (
      <div className="mx-2 mb-2 p-3 rounded-[12px] flex items-center gap-2 animate-pulse" style={{ border: "1px solid var(--color-hairline)" }}>
        <div className="w-6 h-6 rounded bg-[var(--color-muted)] opacity-50" />
        <div className="h-3 w-24 rounded bg-[var(--color-muted)] opacity-50" />
      </div>
    );
  }


  return (
    <div className="mx-2 mb-2 relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-2 rounded-[12px] hover:bg-[rgba(255,255,255,0.05)] transition-colors"
        style={{ border: "1px solid var(--color-hairline)" }}
      >
        <div className="flex items-center gap-2 overflow-hidden">
          <div className="w-6 h-6 rounded flex items-center justify-center bg-[rgba(255,255,255,0.1)] shrink-0">
            <Building size={12} className="text-[var(--color-slate)]" />
          </div>
          <span className="text-label truncate text-white font-medium">
            {activeWorkspace?.name || "Workspace"}
          </span>
        </div>
        <ChevronsUpDown size={14} className="text-[var(--color-slate)] shrink-0" />
      </button>

      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)} 
          />
          <div 
            className="absolute left-0 right-0 bottom-full mb-1 z-50 rounded-[12px] overflow-hidden backdrop-blur-xl shadow-xl border border-[rgba(255,255,255,0.08)] bg-[#13141a]/95"
            style={{ boxShadow: "0 -8px 30px rgba(0,0,0,0.5)" }}
          >
            <div className="py-1">
              {workspaces.map((ws) => (
                <button
                  key={ws.id}
                  onClick={() => {
                    setActiveWorkspaceId(ws.id);
                    setIsOpen(false);
                  }}
                  className="w-full text-left px-3 py-2 text-label flex items-center justify-between hover:bg-[rgba(255,255,255,0.05)] transition-colors"
                >
                  <span className={cn(
                    "truncate",
                    activeWorkspaceId === ws.id ? "text-white" : "text-[var(--color-slate)]"
                  )}>
                    {ws.name}
                  </span>
                  {activeWorkspaceId === ws.id && <Check size={14} className="text-purple-400" />}
                </button>
              ))}
            </div>
            
            <div className="border-t border-[rgba(255,255,255,0.05)] p-1">
              <button 
                className="w-full text-left px-3 py-2 text-label flex items-center gap-2 text-[var(--color-slate)] hover:text-white hover:bg-[rgba(255,255,255,0.05)] rounded-md transition-colors"
                onClick={() => {
                  setIsOpen(false);
                  // Open create workspace modal (not implemented yet)
                }}
              >
                <Plus size={14} />
                <span>Create Workspace</span>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
