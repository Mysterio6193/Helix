"use client";

import React, { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { Command } from "cmdk";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Folder, Zap, Play, Terminal, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { api, type Brand, type RunSummary, type SkillSummary } from "@/lib/api";

interface CommandPaletteContextType {
  open: boolean;
  setOpen: (open: boolean) => void;
}

const CommandPaletteContext = createContext<CommandPaletteContextType | undefined>(undefined);

export function useCommandPalette() {
  const context = useContext(CommandPaletteContext);
  if (!context) {
    throw new Error("useCommandPalette must be used within a CommandPaletteProvider");
  }
  return context;
}

export function CommandPaletteProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  return (
    <CommandPaletteContext.Provider value={{ open, setOpen }}>
      {children}
      <CommandPalette />
    </CommandPaletteContext.Provider>
  );
}

function CommandPalette() {
  const { open, setOpen } = useCommandPalette();
  const router = useRouter();
  const [search, setSearch] = useState("");
  
  const [brands, setBrands] = useState<Brand[]>([]);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [skills, setSkills] = useState<SkillSummary[]>([]);
  const [loading, setLoading] = useState(false);

  // Fetch entities once when search palette is opened
  useEffect(() => {
    if (!open) return;

    async function fetchData() {
      try {
        setLoading(true);
        const [brandList, runList, skillCatalog] = await Promise.all([
          api.brands.list().catch(() => []),
          api.runs.list({ limit: 10 }).catch(() => []),
          api.skills.list().catch(() => ({ items: [] })),
        ]);
        setBrands(brandList);
        setRuns(runList);
        setSkills(skillCatalog.items);
      } catch (err) {
        console.error("Failed to load search index", err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [open]);

  const handleSelect = (url: string) => {
    router.push(url);
    setOpen(false);
    setSearch("");
  };

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]">
          {/* Backdrop Blur overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setOpen(false)}
            className="absolute inset-0 bg-neutral-950/60 backdrop-blur-sm"
          />

          {/* Modal Container */}
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: -8 }}
            transition={{ duration: 0.18, ease: "easeOut" }}
            className="relative w-full max-w-lg overflow-hidden rounded-2xl border border-neutral-200/80 dark:border-neutral-800/80 bg-white/95 dark:bg-neutral-900/95 shadow-2xl backdrop-blur-md"
          >
            <Command className="flex flex-col h-full">
              {/* Top Search Input Bar */}
              <div className="flex items-center gap-3 px-4 border-b border-neutral-200/60 dark:border-neutral-800/60">
                <Search className="w-5 h-5 text-neutral-400" />
                <Command.Input
                  value={search}
                  onValueChange={setSearch}
                  placeholder="Search brands, workflow runs, creative skills..."
                  className="w-full py-4 text-sm bg-transparent outline-none border-none placeholder-neutral-400 text-neutral-800 dark:text-neutral-200"
                />
                <button
                  onClick={() => setOpen(false)}
                  className="p-1 rounded-md hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-400 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Scrollable Results List */}
              <Command.List className="max-h-[300px] overflow-y-auto p-2 scrollbar-thin scrollbar-thumb-neutral-200 dark:scrollbar-thumb-neutral-800">
                <Command.Empty className="py-8 text-center text-sm text-neutral-400 font-medium">
                  {loading ? "Compiling results..." : "No matching assets found"}
                </Command.Empty>

                {/* Brands Section */}
                {brands.length > 0 && (
                  <Command.Group heading="Brands" className="px-2 py-1.5 text-[10px] font-bold text-neutral-400 dark:text-neutral-500 uppercase tracking-widest font-mono">
                    {brands.map((brand) => (
                      <Command.Item
                        key={brand.id}
                        onSelect={() => handleSelect(`/brands/${brand.id}`)}
                        className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100/80 dark:hover:bg-neutral-800/80 cursor-pointer select-none transition-all duration-150 aria-selected:bg-neutral-100 dark:aria-selected:bg-neutral-800"
                      >
                        <Folder className="w-4 h-4 text-indigo-500" />
                        <span className="font-medium">{brand.name}</span>
                      </Command.Item>
                    ))}
                  </Command.Group>
                )}

                {/* Runs Section */}
                {runs.length > 0 && (
                  <Command.Group heading="Recent Workflow Runs" className="px-2 py-1.5 mt-2 text-[10px] font-bold text-neutral-400 dark:text-neutral-500 uppercase tracking-widest font-mono">
                    {runs.map((run) => (
                      <Command.Item
                        key={run.id}
                        onSelect={() => handleSelect(`/workflows/${run.id}`)}
                        className="flex items-center justify-between px-3 py-2.5 rounded-lg text-sm text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100/80 dark:hover:bg-neutral-800/80 cursor-pointer select-none transition-all duration-150 aria-selected:bg-neutral-100 dark:aria-selected:bg-neutral-800"
                      >
                        <div className="flex items-center gap-3">
                          <Play className="w-4 h-4 text-emerald-500 fill-emerald-500/20" />
                          <span className="font-medium truncate max-w-[220px]">
                            {run.workflow.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                          </span>
                        </div>
                        <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full font-mono ${
                          run.status === "completed" 
                            ? "bg-green-50 text-green-600 dark:bg-green-950/30 dark:text-green-400"
                            : run.status === "failed"
                            ? "bg-red-50 text-red-600 dark:bg-red-950/30 dark:text-red-400"
                            : "bg-amber-50 text-amber-600 dark:bg-amber-950/30 dark:text-amber-400"
                        }`}>
                          {run.status}
                        </span>
                      </Command.Item>
                    ))}
                  </Command.Group>
                )}

                {/* Skills Section */}
                {skills.length > 0 && (
                  <Command.Group heading="Creative OS Skills" className="px-2 py-1.5 mt-2 text-[10px] font-bold text-neutral-400 dark:text-neutral-500 uppercase tracking-widest font-mono">
                    {skills.map((skill) => (
                      <Command.Item
                        key={skill.id}
                        onSelect={() => handleSelect(`/skills`)}
                        className="flex items-center justify-between px-3 py-2.5 rounded-lg text-sm text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100/80 dark:hover:bg-neutral-800/80 cursor-pointer select-none transition-all duration-150 aria-selected:bg-neutral-100 dark:aria-selected:bg-neutral-800"
                      >
                        <div className="flex items-center gap-3">
                          <Zap className="w-4 h-4 text-violet-500 fill-violet-500/20" />
                          <span className="font-medium">{skill.name}</span>
                        </div>
                        <span className="text-[10px] text-neutral-400 font-medium">
                          v{skill.version}
                        </span>
                      </Command.Item>
                    ))}
                  </Command.Group>
                )}
              </Command.List>

              {/* Bottom Footer Help Bar */}
              <div className="flex items-center justify-between px-4 py-2 border-t border-neutral-200/60 dark:border-neutral-800/60 bg-neutral-50 dark:bg-neutral-900/40 text-[10px] text-neutral-400 font-medium">
                <div className="flex items-center gap-1">
                  <span className="px-1.5 py-0.5 rounded bg-neutral-200 dark:bg-neutral-800 font-mono text-[9px]">↑↓</span>
                  <span>Navigate</span>
                  <span className="px-1.5 py-0.5 rounded bg-neutral-200 dark:bg-neutral-800 font-mono text-[9px] ml-1">⏎</span>
                  <span>Select</span>
                </div>
                <div className="flex items-center gap-1 font-mono">
                  <span>esc to close</span>
                </div>
              </div>
            </Command>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
