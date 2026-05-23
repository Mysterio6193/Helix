"use client";

import React, { useEffect, useState, useRef } from "react";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";
import { Card, CardTitle, CardSubtitle } from "@/components/ui/card";
import { AlertCircle, RefreshCw, ZoomIn, ZoomOut, Maximize2 } from "lucide-react";

// Dynamically import react-force-graph-2d to prevent SSR failures
const ForceGraph2D = dynamic(
  () => import("react-force-graph-2d").then((mod) => mod.default),
  { ssr: false }
);

interface ForceGraphProps {
  brandId: string;
  className?: string;
}

export function ForceGraph({ brandId, className = "" }: ForceGraphProps) {
  const fgRef = useRef<any>(null);
  const [data, setData] = useState<{ nodes: any[]; links: any[] }>({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  // Fetch brand memory graph data
  useEffect(() => {
    let active = true;

    async function loadGraph() {
      try {
        setLoading(true);
        setError(false);
        const res = await api.memory.graph(brandId, 2);
        
        if (!active) return;

        // Color maps for node styling matching designer palette
        const colors = {
          brand: "#6366f1",    // Indigo
          asset: "#8b5cf6",    // Violet
          learning: "#f59e0b", // Amber
          run: "#14b8a6",      // Teal
        };

        const processedNodes = res.nodes.map((n: any) => ({
          ...n,
          color: colors[n.type as keyof typeof colors] || "#64748b",
          size: n.val ? n.val / 2 : 8,
        }));

        setData({ nodes: processedNodes, links: res.edges });
      } catch (err) {
        console.error("Failed to load memory graph", err);
        if (active) setError(true);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadGraph();
    return () => {
      active = false;
    };
  }, [brandId]);

  // Center / Zoom controls
  const handleZoomIn = () => {
    const fg = fgRef.current;
    if (fg) fg.zoom(fg.zoom() * 1.3, 400);
  };

  const handleZoomOut = () => {
    const fg = fgRef.current;
    if (fg) fg.zoom(fg.zoom() / 1.3, 400);
  };

  const handleCenter = () => {
    const fg = fgRef.current;
    if (fg) fg.centerAt(0, 0, 400);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50/50 dark:bg-neutral-900/50">
        <RefreshCw className="w-8 h-8 text-neutral-400 animate-spin" />
        <span className="text-sm font-medium text-neutral-400 mt-3">Compiling brand memory neural graph...</span>
      </div>
    );
  }

  return (
    <Card className={`relative flex flex-col overflow-hidden h-[500px] p-0 border border-neutral-200/80 dark:border-neutral-800/80 ${className}`}>
      {/* Title Details Overlay */}
      <div className="absolute top-6 left-6 z-10 pointer-events-none">
        <CardTitle className="text-neutral-800 dark:text-neutral-100">Brand Memory Graph</CardTitle>
        <CardSubtitle className="mt-1">
          Force-directed mapping of active runs, distilled learnings, and produced assets.
        </CardSubtitle>
      </div>

      {/* Control Buttons Toolbar */}
      <div className="absolute top-6 right-6 z-10 flex items-center gap-1.5 bg-white/90 dark:bg-neutral-900/90 border border-neutral-200/50 dark:border-neutral-800/50 p-1 rounded-xl shadow-sm backdrop-blur-md">
        <button
          onClick={handleZoomIn}
          className="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-600 dark:text-neutral-300 transition-colors"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          onClick={handleZoomOut}
          className="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-600 dark:text-neutral-300 transition-colors"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          onClick={handleCenter}
          className="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-600 dark:text-neutral-300 transition-colors"
          title="Recenter"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
      </div>

      {/* Legend Indicator Overlay */}
      <div className="absolute bottom-6 left-6 z-10 flex flex-wrap items-center gap-4 bg-white/90 dark:bg-neutral-900/90 border border-neutral-200/50 dark:border-neutral-800/50 px-4 py-2 rounded-xl shadow-sm backdrop-blur-md text-[10px] font-bold font-mono tracking-wide uppercase text-neutral-500">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-indigo-500" />
          <span>Brand Context</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-teal-500" />
          <span>Workflow Run</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-violet-500" />
          <span>S3 Asset</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-amber-500" />
          <span>Learnings</span>
        </div>
      </div>

      {/* Force-directed Canvas Container */}
      <div className="flex-1 w-full h-full bg-neutral-50 dark:bg-neutral-950">
        <ForceGraph2D
          ref={fgRef}
          graphData={data}
          nodeRelSize={6}
          nodeVal="size"
          linkColor={() => "rgba(148, 163, 184, 0.15)"}
          linkWidth={1.5}
          cooldownTicks={100}
          d3AlphaDecay={0.03}
          d3VelocityDecay={0.3}
          nodeCanvasObject={(node: any, ctx, globalScale) => {
            const label = node.label || "";
            const fontSize = Math.max(9 / globalScale, 2.5);
            ctx.font = `${fontSize}px Inter, sans-serif`;

            // Draw colored node circle background
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.size || 4, 0, 2 * Math.PI, false);
            ctx.fillStyle = node.color || "#64748b";
            ctx.fill();
            
            // Draw subtle ring highlight
            ctx.lineWidth = 1.5 / globalScale;
            ctx.strokeStyle = "rgba(255, 255, 255, 0.9)";
            ctx.stroke();

            // Render node labels
            if (globalScale > 0.8) {
              ctx.textAlign = "center";
              ctx.textBaseline = "middle";
              ctx.fillStyle = "rgba(100, 116, 139, 0.85)";
              
              // Draw simple label text beneath the node circle
              ctx.fillText(label, node.x, node.y + (node.size || 4) + 6);
            }
          }}
        />
      </div>
    </Card>
  );
}
