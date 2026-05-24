"use client";

import { useState } from "react";
import useSWR from "swr";
import { motion, AnimatePresence } from "framer-motion";
import {
  Camera,
  Clapperboard,
  Copy,
  Film,
  Image as ImageIcon,
  Layers,
  Loader2,
  Play,
  Plus,
  RefreshCw,
  Sparkles,
  Trash2,
  Video,
  X,
  Zap,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

const JOB_STATUS_COLORS: Record<string, "neutral" | "success" | "warning" | "error" | "info"> = {
  pending: "neutral",
  running: "info",
  completed: "success",
  failed: "error",
  cancelled: "neutral",
};

export default function MediaConsolePage() {
  const [activeTab, setActiveTab] = useState<"generate" | "jobs" | "templates">("generate");
  const [generationType, setGenerationType] = useState<"image" | "video">("image");
  const [prompt, setPrompt] = useState("");
  const [batchPrompts, setBatchPrompts] = useState("");
  const [model, setModel] = useState("");
  const [generating, setGenerating] = useState(false);
  const [lastResult, setLastResult] = useState<any>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<any>(null);
  const [templateVars, setTemplateVars] = useState<Record<string, string>>({});

  const { data: jobs, mutate: mutateJobs } = useSWR(
    "media-jobs",
    () => api.media.jobs(),
    { refreshInterval: 5000 }
  );

  const { data: templates } = useSWR(
    "media-templates",
    () => api.media.templates(),
    { revalidateOnFocus: false }
  );

  const { data: catalog } = useSWR(
    "llm-catalog",
    () => api.llm.catalog(),
    { revalidateOnFocus: false }
  );

  const imageModels = catalog?.models?.filter((m: any) => m.capability === "image") || [];
  const videoModels = catalog?.models?.filter((m: any) => m.capability === "video") || [];

  async function generateSingle() {
    if (!prompt.trim()) return;
    setGenerating(true);
    try {
      if (generationType === "image") {
        const result = await api.llm.images({
          prompt,
          model: model || undefined,
          size: "1024x1024",
          quality: "high",
          n: 1,
        });
        setLastResult({ type: "image", ...result });
      } else {
        const result = await api.llm.videos({
          prompt,
          model: model || undefined,
          duration_seconds: 5,
          aspect_ratio: "16:9",
        });
        setLastResult({ type: "video", ...result });
      }
    } catch (e) {
      console.error(e);
      alert("Generation failed: " + (e as any)?.message);
    } finally {
      setGenerating(false);
    }
  }

  async function createBatchJob() {
    if (!batchPrompts.trim()) return;
    const prompts = batchPrompts
      .split("\n")
      .map((p) => p.trim())
      .filter((p) => p.length > 0);
    if (prompts.length === 0) return;

    try {
      const job = await api.media.createJob({
        name: `Batch ${generationType} generation (${prompts.length} items)`,
        job_type: generationType,
        model: model || undefined,
        prompts,
        config:
          generationType === "image"
            ? { size: "1024x1024", quality: "high" }
            : { duration_seconds: 5, aspect_ratio: "16:9" },
      });

      // Auto-run the job
      await api.media.runJob(job.id);
      mutateJobs();
      setBatchPrompts("");
      setActiveTab("jobs");
    } catch (e) {
      console.error(e);
      alert("Failed to create job: " + (e as any)?.message);
    }
  }

  async function runJob(jobId: string) {
    try {
      await api.media.runJob(jobId);
      mutateJobs();
    } catch (e) {
      console.error(e);
    }
  }

  async function cancelJob(jobId: string) {
    try {
      await api.media.cancelJob(jobId);
      mutateJobs();
    } catch (e) {
      console.error(e);
    }
  }

  function applyTemplate(template: any) {
    setSelectedTemplate(template);
    setTemplateVars({});
    // Extract variable placeholders like {product}, {brand}, etc.
    const matches = template.prompt_template.match(/\{(\w+)\}/g);
    if (matches) {
      const vars: Record<string, string> = {};
      matches.forEach((match: string) => {
        const key = match.replace(/[{}]/g, "");
        vars[key] = "";
      });
      setTemplateVars(vars);
    }
  }

  function renderTemplatePrompt() {
    if (!selectedTemplate) return "";
    let rendered = selectedTemplate.prompt_template;
    Object.entries(templateVars).forEach(([key, value]) => {
      rendered = rendered.replace(new RegExp(`\\{${key}\\}`, "g"), value || `{${key}}`);
    });
    return rendered;
  }

  function useTemplatePrompt() {
    const rendered = renderTemplatePrompt();
    if (rendered) {
      setPrompt(rendered);
      setGenerationType(selectedTemplate.type === "video" ? "video" : "image");
      setActiveTab("generate");
      setSelectedTemplate(null);
    }
  }

  return (
    <div className="space-y-8 animate-fade-up">
      <header>
        <div className="text-eyebrow text-[color:var(--color-stone)]">
          Generation
        </div>
        <h1 className="mt-2 text-display-lg font-bold leading-tight text-white">
          Media Console
        </h1>
        <p className="mt-3 max-w-[72ch] text-body-md text-[color:var(--color-slate)]">
          Generate images and videos with AI. Create batch jobs, use templates,
          and manage your creative assets in one place.
        </p>
      </header>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-white/[0.06] pb-1">
        {[
          { id: "generate", label: "Generate", icon: Sparkles },
          { id: "jobs", label: "Jobs", icon: Layers },
          { id: "templates", label: "Templates", icon: Copy },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-bold transition-colors border-b-2 -mb-1 ${
              activeTab === tab.id
                ? "text-white border-white"
                : "text-[color:var(--color-slate)] border-transparent hover:text-white"
            }`}
          >
            <tab.icon className="size-4" />
            {tab.label}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {activeTab === "generate" && (
          <motion.div
            key="generate"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_0.4fr]"
          >
            <div className="space-y-6">
              <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
                <div className="mb-5 flex items-center justify-between">
                  <div>
                    <div className="text-eyebrow text-[color:var(--color-stone)]">
                      Create
                    </div>
                    <h2 className="mt-1 text-heading-lg text-white">
                      {generationType === "image" ? "Image Generation" : "Video Generation"}
                    </h2>
                  </div>
                  <div className="flex gap-1 rounded-lg border border-white/[0.06] bg-black/20 p-1">
                    <button
                      onClick={() => setGenerationType("image")}
                      className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-bold transition ${
                        generationType === "image"
                          ? "bg-white/10 text-white"
                          : "text-[color:var(--color-slate)] hover:text-white"
                      }`}
                    >
                      <ImageIcon className="size-3.5" />
                      Image
                    </button>
                    <button
                      onClick={() => setGenerationType("video")}
                      className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-bold transition ${
                        generationType === "video"
                          ? "bg-white/10 text-white"
                          : "text-[color:var(--color-slate)] hover:text-white"
                      }`}
                    >
                      <Video className="size-3.5" />
                      Video
                    </button>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-bold text-[color:var(--color-stone)] mb-1.5 block">
                      Model
                    </label>
                    <select
                      value={model}
                      onChange={(e) => setModel(e.target.value)}
                      className="w-full rounded-lg border border-white/[0.06] bg-black/20 px-3 py-2 text-sm text-white focus:outline-none focus:border-white/20"
                    >
                      <option value="">Default ({generationType === "image" ? "GPT-Image-1" : "Veo 3"})</option>
                      {(generationType === "image" ? imageModels : videoModels).map((m: any) => (
                        <option key={m.id} value={m.id}>
                          {m.display_name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-bold text-[color:var(--color-stone)] mb-1.5 block">
                      Prompt
                    </label>
                    <textarea
                      placeholder={`Describe the ${generationType} you want to generate...`}
                      value={prompt}
                      onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setPrompt(e.target.value)}
                      rows={4}
                      className="w-full rounded-lg border border-white/[0.06] bg-black/20 px-3 py-2 text-sm text-white placeholder:text-[color:var(--color-stone)] focus:outline-none focus:border-white/20 resize-y"
                    />
                  </div>

                  <div className="flex gap-2">
                    <Button
                      variant="primary"
                      size="md"
                      onClick={generateSingle}
                      disabled={!prompt.trim() || generating}
                      className="flex-1"
                    >
                      {generating ? (
                        <>
                          <Loader2 className="size-4 animate-spin" />
                          Generating...
                        </>
                      ) : (
                        <>
                          <Zap className="size-4" />
                          Generate {generationType === "image" ? "Image" : "Video"}
                        </>
                      )}
                    </Button>
                  </div>
                </div>

                {/* Result */}
                {lastResult && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-6 rounded-lg border border-white/[0.06] bg-black/20 p-4"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs font-bold text-white">
                        Result
                      </span>
                      <Badge tone="success">{lastResult.type}</Badge>
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                      {lastResult.type === "image" && lastResult.images?.map((img: any, i: number) => (
                        <div key={i} className="relative aspect-square rounded-lg overflow-hidden bg-black/40">
                          <img
                            src={`/api/v1/assets/${img.s3_key}/url`}
                            alt={`Generated ${i + 1}`}
                            className="w-full h-full object-cover"
                            onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
                              e.currentTarget.src = `https://placehold.co/400x400/1a1a2e/white?text=Image+${i+1}`;
                            }}
                          />
                        </div>
                      ))}
                      {lastResult.type === "video" && lastResult.videos?.map((vid: any, i: number) => (
                        <div key={i} className="relative aspect-video rounded-lg overflow-hidden bg-black/40 flex items-center justify-center">
                          <Clapperboard className="size-12 text-[color:var(--color-stone)]" />
                          <span className="absolute bottom-2 left-2 text-[10px] text-white bg-black/60 px-1.5 py-0.5 rounded">
                            {vid.duration_seconds}s
                          </span>
                        </div>
                      ))}
                    </div>
                    {lastResult.cost_usd && (
                      <p className="mt-2 text-[10px] text-[color:var(--color-stone)]">
                        Cost: ${lastResult.cost_usd.toFixed(4)}
                      </p>
                    )}
                  </motion.div>
                )}
              </Card>

              <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
                <div className="mb-5">
                  <div className="text-eyebrow text-[color:var(--color-stone)]">
                    Batch
                  </div>
                  <h2 className="mt-1 text-heading-lg text-white">Bulk Generation</h2>
                </div>

                <p className="text-sm text-[color:var(--color-slate)] mb-3">
                  Enter one prompt per line to create a batch job.
                </p>

                <textarea
                  placeholder={`Product photo on white background\nLifestyle shot in kitchen\nClose-up detail shot...`}
                  value={batchPrompts}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setBatchPrompts(e.target.value)}
                  rows={6}
                  className="mb-3 w-full rounded-lg border border-white/[0.06] bg-black/20 px-3 py-2 text-sm text-white placeholder:text-[color:var(--color-stone)] focus:outline-none focus:border-white/20 resize-y"
                />

                <div className="flex items-center justify-between">
                  <span className="text-xs text-[color:var(--color-stone)]">
                    {batchPrompts.split("\n").filter((p) => p.trim()).length} prompts
                  </span>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={createBatchJob}
                    disabled={!batchPrompts.trim()}
                  >
                    <Plus className="size-3.5" />
                    Create Batch Job
                  </Button>
                </div>
              </Card>
            </div>

            <div className="space-y-6">
              <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
                <div className="mb-4">
                  <div className="text-eyebrow text-[color:var(--color-stone)]">Status</div>
                  <h2 className="mt-1 text-heading-lg text-white">System</h2>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-[color:var(--color-slate)]">Image Models</span>
                    <Badge tone="info">{imageModels.length}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-[color:var(--color-slate)]">Video Models</span>
                    <Badge tone="info">{videoModels.length}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-[color:var(--color-slate)]">Active Jobs</span>
                    <Badge tone="info">
                      {jobs?.filter((j: any) => j.status === "running").length || 0}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-[color:var(--color-slate)]">Completed</span>
                    <Badge tone="success">
                      {jobs?.filter((j: any) => j.status === "completed").length || 0}
                    </Badge>
                  </div>
                </div>
              </Card>

              {selectedTemplate && (
                <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
                  <div className="mb-4 flex items-center justify-between">
                    <div>
                      <div className="text-eyebrow text-[color:var(--color-stone)]">Template</div>
                      <h2 className="mt-1 text-heading-lg text-white">{selectedTemplate.name}</h2>
                    </div>
                    <Button variant="secondary" size="sm" onClick={() => setSelectedTemplate(null)}>
                      <X className="size-4" />
                    </Button>
                  </div>

                  <div className="space-y-3 mb-4">
                    {Object.keys(templateVars).map((key) => (
                      <div key={key}>
                        <label className="text-xs font-bold text-[color:var(--color-stone)] mb-1 block capitalize">
                          {key}
                        </label>
                        <Input
                          value={templateVars[key]}
                          onChange={(e) =>
                            setTemplateVars((prev) => ({ ...prev, [key]: e.target.value }))
                          }
                          placeholder={`Enter ${key}...`}
                        />
                      </div>
                    ))}
                  </div>

                  <div className="rounded-lg border border-white/[0.06] bg-black/20 p-3 mb-4">
                    <p className="text-[10px] text-[color:var(--color-stone)] mb-1">Preview:</p>
                    <p className="text-xs text-white">{renderTemplatePrompt()}</p>
                  </div>

                  <Button variant="primary" size="sm" className="w-full" onClick={useTemplatePrompt}>
                    <Sparkles className="size-3.5" />
                    Use This Prompt
                  </Button>
                </Card>
              )}
            </div>
          </motion.div>
        )}

        {activeTab === "jobs" && (
          <motion.div
            key="jobs"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <div className="text-eyebrow text-[color:var(--color-stone)]">Queue</div>
                  <h2 className="mt-1 text-heading-lg text-white">Generation Jobs</h2>
                </div>
                <Button variant="secondary" size="sm" onClick={() => mutateJobs()}>
                  <RefreshCw className="size-3.5" />
                  Refresh
                </Button>
              </div>

              <div className="space-y-3">
                {jobs?.map((job: any) => (
                  <motion.div
                    key={job.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="rounded-lg border border-white/[0.06] bg-black/20 p-4"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {job.job_type === "image" ? (
                          <ImageIcon className="size-5 text-[color:var(--color-slate)]" />
                        ) : job.job_type === "video" ? (
                          <Film className="size-5 text-[color:var(--color-slate)]" />
                        ) : (
                          <Layers className="size-5 text-[color:var(--color-slate)]" />
                        )}
                        <div>
                          <h3 className="text-sm font-bold text-white">{job.name}</h3>
                          <p className="text-[10px] text-[color:var(--color-stone)]">
                            {job.job_type} · {job.total_items} items · {job.model || "default"}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge tone={JOB_STATUS_COLORS[job.status] || "neutral"}>
                          {job.status}
                        </Badge>
                        {job.status === "pending" && (
                          <Button variant="primary" size="sm" onClick={() => runJob(job.id)}>
                            <Play className="size-3" />
                          </Button>
                        )}
                        {job.status === "running" && (
                          <Button variant="secondary" size="sm" onClick={() => cancelJob(job.id)}>
                            <X className="size-3" />
                          </Button>
                        )}
                      </div>
                    </div>

                    {job.status === "running" && (
                      <div className="mt-3">
                        <div className="h-1.5 rounded-full bg-black/40 overflow-hidden">
                          <div
                            className="h-full rounded-full bg-emerald-400 transition-all"
                            style={{
                              width: `${(job.completed_items / job.total_items) * 100}%`,
                            }}
                          />
                        </div>
                        <div className="flex justify-between mt-1">
                          <span className="text-[10px] text-[color:var(--color-stone)]">
                            {job.completed_items} / {job.total_items}
                          </span>
                          <span className="text-[10px] text-[color:var(--color-stone)]">
                            {job.failed_items > 0 && `${job.failed_items} failed`}
                          </span>
                        </div>
                      </div>
                    )}

                    {job.status === "completed" && job.results?.length > 0 && (
                      <div className="mt-3 grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-2">
                        {job.results.map((result: any, i: number) => (
                          <div
                            key={i}
                            className="aspect-square rounded-lg overflow-hidden bg-black/40 relative"
                          >
                            {result.type === "image" ? (
                              <img
                                src={`/api/v1/assets/${result.s3_key}/url`}
                                alt={`Result ${i + 1}`}
                                className="w-full h-full object-cover"
                                onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
                                  e.currentTarget.src = `https://placehold.co/200x200/1a1a2e/white?text=${i+1}`;
                                }}
                              />
                            ) : result.type === "video" ? (
                              <div className="w-full h-full flex items-center justify-center">
                                <Film className="size-6 text-[color:var(--color-stone)]" />
                              </div>
                            ) : (
                              <div className="w-full h-full flex items-center justify-center">
                                <span className="text-[10px] text-rose-400">!</span>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    {job.total_cost_usd && (
                      <p className="mt-2 text-[10px] text-[color:var(--color-stone)]">
                        Cost: ${job.total_cost_usd.toFixed(4)}
                      </p>
                    )}
                  </motion.div>
                ))}

                {!jobs?.length && (
                  <div className="text-center py-12">
                    <Layers className="mx-auto size-8 text-[color:var(--color-stone)]" />
                    <p className="mt-3 text-sm text-[color:var(--color-slate)]">
                      No generation jobs yet. Create one from the Generate tab.
                    </p>
                  </div>
                )}
              </div>
            </Card>
          </motion.div>
        )}

        {activeTab === "templates" && (
          <motion.div
            key="templates"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <Card className="rounded-lg border-white/[0.06] bg-[#13141a]/60 p-5 shadow-2xl">
              <div className="mb-5">
                <div className="text-eyebrow text-[color:var(--color-stone)]">Library</div>
                <h2 className="mt-1 text-heading-lg text-white">Prompt Templates</h2>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {templates?.map((template: any) => (
                  <div
                    key={template.id}
                    onClick={() => applyTemplate(template)}
                    className="rounded-lg border border-white/[0.06] bg-black/20 p-4 hover:bg-white/[0.02] hover:border-white/10 transition-all cursor-pointer group"
                  >
                    <div className="flex items-center gap-3 mb-3">
                      {template.type === "image" ? (
                        <Camera className="size-5 text-[color:var(--color-slate)]" />
                      ) : template.type === "video" ? (
                        <Clapperboard className="size-5 text-[color:var(--color-slate)]" />
                      ) : (
                        <Layers className="size-5 text-[color:var(--color-slate)]" />
                      )}
                      <div>
                        <h3 className="text-sm font-bold text-white group-hover:text-white">
                          {template.name}
                        </h3>
                        <Badge tone="info" className="text-[8px]">
                          {template.type}
                        </Badge>
                      </div>
                    </div>
                    <p className="text-xs text-[color:var(--color-slate)] mb-2">
                      {template.description}
                    </p>
                    <p className="text-[10px] text-[color:var(--color-stone)] line-clamp-2">
                      {template.prompt_template}
                    </p>
                  </div>
                ))}

                {!templates?.length && (
                  <div className="col-span-full text-center py-12">
                    <Copy className="mx-auto size-8 text-[color:var(--color-stone)]" />
                    <p className="mt-3 text-sm text-[color:var(--color-slate)]">
                      No templates available.
                    </p>
                  </div>
                )}
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
