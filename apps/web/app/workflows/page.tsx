import { RunList } from "@/components/workflow/run-list";

export default function WorkflowsIndex() {
  return (
    <div className="space-y-8">
      <header>
        <div className="text-eyebrow text-[color:var(--color-stone)]">Workspace</div>
        <h1 className="text-display-lg text-[color:var(--color-charcoal)]">
          Workflows
        </h1>
        <p className="mt-2 text-body-md text-[color:var(--color-slate)] max-w-[60ch]">
          Every run is a Helix execution plan with live status, checkpoints,
          agent actions, artifacts, and replayable history.
        </p>
      </header>
      <RunList limit={40} />
    </div>
  );
}
