"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Image, FileText, Layout, Video, File, RefreshCw } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface AssetThumbProps {
  assetId: string;
  kind: string;
  mimeType?: string | null;
  className?: string;
}

export function AssetThumb({ assetId, kind, mimeType, className = "" }: AssetThumbProps) {
  const [thumbUrl, setThumbUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadThumbnail() {
      try {
        setLoading(true);
        setError(false);
        const res = await api.assets.thumbnail(assetId);
        if (active) {
          setThumbUrl(res.url);
        }
      } catch (err) {
        console.error("Failed to load thumbnail", err);
        if (active) setError(true);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadThumbnail();
    return () => {
      active = false;
    };
  }, [assetId]);

  // Determine standard icons for mime-types or kinds if image is not loaded / is fallback
  const getFallbackIcon = () => {
    const k = kind.toLowerCase();
    const m = (mimeType || "").toLowerCase();

    if (m.startsWith("image/") || k.includes("logo") || k.includes("palette")) {
      return <Image className="w-6 h-6 text-neutral-400" />;
    }
    if (m.includes("html") || k.includes("web") || k.includes("site") || k.includes("landing")) {
      return <Layout className="w-6 h-6 text-indigo-400" />;
    }
    if (m.startsWith("video/")) {
      return <Video className="w-6 h-6 text-rose-400" />;
    }
    if (m.startsWith("text/") || k.includes("copy") || k.includes("slogan")) {
      return <FileText className="w-6 h-6 text-amber-400" />;
    }
    return <File className="w-6 h-6 text-neutral-400" />;
  };

  const isImageFormat = () => {
    const m = (mimeType || "").toLowerCase();
    const k = kind.toLowerCase();
    // Assets that generate visually displayable web images
    return m.startsWith("image/") || k.includes("logo") || k.includes("variant") || k.includes("palette") || thumbUrl?.startsWith("http");
  };

  return (
    <div className={`relative flex items-center justify-center overflow-hidden bg-neutral-100 dark:bg-neutral-900 border border-neutral-200/60 dark:border-neutral-800/60 rounded-xl transition-all duration-300 ${className}`}>
      <AnimatePresence mode="wait">
        {loading ? (
          // Shimmer Skeleton Loader
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 flex items-center justify-center bg-neutral-150 dark:bg-neutral-850"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" style={{ backgroundSize: "200% 100%" }} />
            <RefreshCw className="w-4 h-4 text-neutral-400 animate-spin" />
          </motion.div>
        ) : error || !thumbUrl || !isImageFormat() ? (
          // Generic Icon Fallback
          <motion.div
            key="fallback"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center gap-1 p-2 text-center"
          >
            {getFallbackIcon()}
            <span className="text-[9px] font-bold text-neutral-400 font-mono tracking-wider uppercase truncate max-w-[80px]">
              {kind.replace(/_/g, " ")}
            </span>
          </motion.div>
        ) : (
          // WebP Thumbnail Image
          <motion.img
            key="image"
            src={thumbUrl}
            alt={kind}
            initial={{ opacity: 0, scale: 1.05 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="w-full h-full object-cover"
            onError={() => setError(true)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
