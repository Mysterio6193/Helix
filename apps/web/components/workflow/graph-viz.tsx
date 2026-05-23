"use client";

import React, { useEffect, useState, useMemo } from "react";
import {
  ReactFlow,
  Controls,
  Background,
  Panel,
  useNodesState,
  useEdgesState,
  Position,
  Handle,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { motion, AnimatePresence } from "framer-motion";
import { Play, CheckCircle2, XCircle, AlertCircle, RefreshCw, Layers } from "lucide-react";
import { api, type RunDetail } from "@/lib/api";
import { useRunStream } from "@/lib/ws";

// Custom premium Workflow node type
const CustomNode = ({ data }: any) => {
  const { label, status, agent, criticScore, active } = data;

  const statusConfig = {
    completed: {
      borderClass: "border-green-500/50 dark:border-green-400/50 bg-green-50/80 dark:bg-green-950/20",
      textClass: "text-green-700 dark:text-green-300",
      icon: <CheckCircle2 className="w-4 h-4 text-green-500" />,
      glow: "shadow-[0_0_15px_rgba(34,197,94,0.15)]",
    },
    running: {
      borderClass: "border-amber-500/50 dark:border-amber-400/50 bg-amber-50/80 dark:bg-amber-950/20 animate-pulse",
      textClass: "text-amber-700 dark:text-amber-300",
      icon: <RefreshCw className="w-4 h-4 text-amber-500 animate-spin" />,
      glow: "shadow-[0_0_20px_rgba(245,158,11,0.25)] ring-2 ring-amber-500/30",
    },
    failed: {
      borderClass: "border-red-500/50 dark:border-red-400/50 bg-red-50/80 dark:bg-red-950/20",
      textClass: "text-red-700 dark:text-red-300",
      icon: <XCircle className="w-4 h-4 text-red-500" />,
      glow: "shadow-[0_0_15px_rgba(239,68,68,0.15)]",
    },
    pending: {
      borderClass: "border-neutral-200 dark:border-neutral-800 bg-white/90 dark:bg-neutral-900/90",
      textClass: "text-neutral-500 dark:text-neutral-400",
      icon: <Layers className="w-4 h-4 text-neutral-400" />,
      glow: "shadow-sm",
    },
  };

  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;

  return (
    <div
      className={`relative flex items-center gap-3 px-4 py-3 rounded-xl border backdrop-blur-md transition-all duration-300 min-w-[200px] ${config.borderClass} ${config.glow}`}
    >
      <Handle type="target" position={Position.Left} className="!bg-neutral-300 dark:!bg-neutral-700 !w-2 !h-2" />
      
      <div className="flex items-center justify-center p-1.5 rounded-lg bg-white dark:bg-neutral-800 shadow-sm border border-neutral-100 dark:border-neutral-700">
        {config.icon}
      </div>

      <div className="flex flex-col text-left">
        <span className={`text-xs font-semibold tracking-wide truncate ${config.textClass}`}>
          {label}
        </span>
        {agent && (
          <span className="text-[10px] text-neutral-400 dark:text-neutral-500 font-medium font-mono uppercase tracking-wider">
            {agent}
          </span>
        )}
      </div>

      {criticScore !== undefined && (
        <span className="absolute -top-2 -right-2 flex items-center justify-center text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-indigo-500 text-white shadow-md border border-indigo-400/30">
          ★ {criticScore}
        </span>
      )}

      {active && (
        <span className="absolute -top-1 -left-1 flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
        </span>
      )}

      <Handle type="source" position={Position.Right} className="!bg-neutral-300 dark:!bg-neutral-700 !w-2 !h-2" />
    </div>
  );
};

const nodeTypes = {
  workflowNode: CustomNode,
};

interface GraphVizProps {
  runId: string;
  workflowSlice: string;
  className?: string;
}

export function GraphViz({ runId, workflowSlice, className = "" }: GraphVizProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<any>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<any>([]);
  const [loading, setLoading] = useState(true);

  // Connect to the real-time websocket event stream
  const { events } = useRunStream(runId);

  // Compile active node state from stream events
  const runState = useMemo(() => {
    const statuses: Record<string, { status: "completed" | "running" | "failed" | "pending"; agent?: string; score?: number }> = {};
    
    // Process all events sequentially to compute step status
    for (const event of events) {
      const type = event.type || "";
      const p = (event.payload || {}) as Record<string, any>;
      const stepName = p.skill || p.step || "";

      if (!stepName) continue;

      // Map start/completion events
      if (type.endsWith(".started")) {
        statuses[stepName] = {
          status: "running",
          agent: p.agent || undefined,
        };
      } else if (type.endsWith(".completed")) {
        statuses[stepName] = {
          status: "completed",
          agent: p.agent || undefined,
          score: p.critic_score || undefined,
        };
      } else if (type.endsWith(".failed")) {
        statuses[stepName] = {
          status: "failed",
          agent: p.agent || undefined,
        };
      }
    }
    return statuses;
  }, [events]);

  // Load the graph structure from backend
  useEffect(() => {
    let active = true;

    async function loadGraph() {
      try {
        setLoading(true);
        const data = await api.workflows.graph(workflowSlice);
        if (!active) return;

        // Position nodes in a logical horizontal flow
        const positionedNodes = data.nodes.map((node: any, idx: number) => {
          const row = idx % 2;
          const col = Math.floor(idx / 2);
          
          return {
            id: node.id,
            type: "workflowNode",
            position: { x: idx * 250 + 50, y: row * 100 + 100 },
            data: {
              label: node.label,
              status: "pending",
              active: false,
            },
          };
        });

        // Set standard smooth edges
        const stylizedEdges = data.edges.map((edge: any) => ({
          ...edge,
          animated: false,
          style: { stroke: "#cbd5e1" },
        }));

        setNodes(positionedNodes);
        setEdges(stylizedEdges);
      } catch (err) {
        console.error("Failed to load workflow graph", err);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadGraph();
    return () => {
      active = false;
    };
  }, [workflowSlice, setNodes, setEdges]);

  // Sync node statuses dynamically when stream changes
  useEffect(() => {
    setNodes((prevNodes) =>
      prevNodes.map((node) => {
        const stepName = node.id;
        const state = runState[stepName] || { status: "pending" };
        
        return {
          ...node,
          data: {
            ...node.data,
            status: state.status,
            agent: state.agent,
            criticScore: state.score,
            active: state.status === "running",
          },
        };
      })
    );

    setEdges((prevEdges) =>
      prevEdges.map((edge) => {
        const sourceState = runState[edge.source];
        const targetState = runState[edge.target];
        
        const isAnimated = sourceState?.status === "completed" && targetState?.status === "running";
        const isPassed = sourceState?.status === "completed";

        return {
          ...edge,
          animated: isAnimated,
          style: {
            ...edge.style,
            stroke: isPassed ? "#22c55e" : isAnimated ? "#f59e0b" : "#cbd5e1",
            strokeWidth: isPassed || isAnimated ? 2 : 1.5,
          },
        };
      })
    );
  }, [runState, setNodes, setEdges]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[350px] rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50/50 dark:bg-neutral-900/50">
        <RefreshCw className="w-8 h-8 text-neutral-400 animate-spin" />
        <span className="text-sm font-medium text-neutral-400 mt-3">Compiling workflow graph...</span>
      </div>
    );
  }

  return (
    <div className={`relative h-[350px] w-full border border-neutral-200/80 dark:border-neutral-800/80 bg-neutral-50 dark:bg-neutral-950 rounded-2xl overflow-hidden shadow-sm ${className}`}>
      {/* Title Header Panel */}
      <div className="absolute top-4 left-4 z-10 flex items-center gap-2 px-3 py-1.5 rounded-lg border border-neutral-200/50 dark:border-neutral-800/50 bg-white/95 dark:bg-neutral-900/95 shadow-sm backdrop-blur-md">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
        </span>
        <span className="text-[11px] font-bold text-neutral-600 dark:text-neutral-300 font-mono tracking-wider uppercase">
          Workflow Canvas
        </span>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.5}
        maxZoom={1.5}
        fitViewOptions={{ padding: 0.2 }}
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={16} size={1} color="#e5e5e5" className="dark:opacity-10" />
        <Controls className="!bg-white dark:!bg-neutral-900 !border-neutral-200 dark:!border-neutral-800 !shadow-md !rounded-lg overflow-hidden" />
      </ReactFlow>
    </div>
  );
}
