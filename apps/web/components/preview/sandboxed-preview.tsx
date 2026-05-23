"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { Laptop, Tablet as TabletIcon, Phone, RotateCw, Copy, Check } from "lucide-react";

interface SandboxedPreviewProps {
  html: string;
  title?: string;
  initialViewport?: "desktop" | "tablet" | "mobile";
}

export function SandboxedPreview({
  html,
  title = "Helix Live Preview",
  initialViewport = "desktop",
}: SandboxedPreviewProps) {
  const [viewport, setViewport] = useState<"desktop" | "tablet" | "mobile">(initialViewport);
  const [copied, setCopied] = useState(false);
  const [key, setKey] = useState(0); // For iframe refresh

  const handleCopy = () => {
    navigator.clipboard.writeText(html);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRefresh = () => {
    setKey((prev) => prev + 1);
  };

  const getViewportWidth = () => {
    switch (viewport) {
      case "mobile":
        return "375px";
      case "tablet":
        return "768px";
      case "desktop":
      default:
        return "100%";
    }
  };

  return (
    <div className="flex flex-col h-full rounded-2xl border border-neutral-200/80 dark:border-neutral-800/80 bg-neutral-50 dark:bg-neutral-950 overflow-hidden shadow-xl shadow-neutral-100/50 dark:shadow-none">
      {/* Top Browser Control Bar */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-3 px-4 py-3 border-b border-neutral-200/60 dark:border-neutral-800/60 bg-white dark:bg-neutral-900/60 backdrop-blur-md">
        {/* Mock Window Dots */}
        <div className="flex items-center gap-1.5 self-start md:self-auto">
          <div className="w-3 h-3 rounded-full bg-red-400 dark:bg-red-500/80" />
          <div className="w-3 h-3 rounded-full bg-yellow-400 dark:bg-yellow-500/80" />
          <div className="w-3 h-3 rounded-full bg-green-400 dark:bg-green-500/80" />
        </div>

        {/* Viewport Resizer Controls */}
        <div className="flex items-center gap-1 bg-neutral-100 dark:bg-neutral-800 p-0.5 rounded-lg text-neutral-500 dark:text-neutral-400">
          <button
            onClick={() => setViewport("desktop")}
            className={`flex items-center justify-center p-1.5 rounded-md transition-all ${
              viewport === "desktop"
                ? "bg-white dark:bg-neutral-700 text-neutral-900 dark:text-white shadow-sm"
                : "hover:text-neutral-950 dark:hover:text-neutral-200"
            }`}
            title="Desktop Mode"
          >
            <Laptop className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewport("tablet")}
            className={`flex items-center justify-center p-1.5 rounded-md transition-all ${
              viewport === "tablet"
                ? "bg-white dark:bg-neutral-700 text-neutral-900 dark:text-white shadow-sm"
                : "hover:text-neutral-950 dark:hover:text-neutral-200"
            }`}
            title="Tablet Mode"
          >
            <TabletIcon className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewport("mobile")}
            className={`flex items-center justify-center p-1.5 rounded-md transition-all ${
              viewport === "mobile"
                ? "bg-white dark:bg-neutral-700 text-neutral-900 dark:text-white shadow-sm"
                : "hover:text-neutral-950 dark:hover:text-neutral-200"
            }`}
            title="Mobile Mode"
          >
            <Phone className="w-4 h-4" />
          </button>
        </div>

        {/* Mock Address Bar & Actions */}
        <div className="flex items-center gap-2 w-full md:w-auto self-stretch md:self-auto justify-end">
          <div className="flex-1 md:flex-initial flex items-center bg-neutral-100 dark:bg-neutral-800 px-3 py-1.5 rounded-lg text-xs font-mono text-neutral-500 dark:text-neutral-400 border border-neutral-200/20 max-w-xs overflow-hidden text-ellipsis whitespace-nowrap">
            {title.toLowerCase().replace(/\s+/g, "-")}.helix.local
          </div>

          <button
            onClick={handleRefresh}
            className="flex items-center justify-center p-2 rounded-lg bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-neutral-600 dark:text-neutral-300 transition-all active:scale-95"
            title="Refresh Preview"
          >
            <RotateCw className="w-4 h-4" />
          </button>
          
          <button
            onClick={handleCopy}
            className="flex items-center justify-center p-2 rounded-lg bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-neutral-600 dark:text-neutral-300 transition-all active:scale-95"
            title="Copy Source HTML"
          >
            {copied ? (
              <Check className="w-4 h-4 text-green-500 dark:text-green-400" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Main Iframe Canvas Sandbox */}
      <div className="flex-1 flex items-center justify-center p-4 bg-neutral-100/50 dark:bg-neutral-900/20 overflow-hidden">
        <motion.div
          layout
          style={{ width: getViewportWidth() }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className="h-full border border-neutral-200 dark:border-neutral-800 rounded-xl bg-white dark:bg-white overflow-hidden shadow-2xl"
        >
          {html ? (
            <iframe
              key={key}
              title={title}
              srcDoc={html}
              sandbox="allow-scripts"
              className="w-full h-full border-none bg-white"
            />
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center gap-2 p-6 text-center text-neutral-400 dark:text-neutral-500">
              <Laptop className="w-12 h-12 stroke-[1.2] opacity-40 animate-pulse" />
              <p className="text-sm font-medium">No preview content generated yet</p>
              <p className="text-xs max-w-xs opacity-75">
                Generate website code through an active slice workflow to view sandboxed renders here.
              </p>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
