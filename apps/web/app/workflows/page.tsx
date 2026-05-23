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
          Every run is a LangGraph executed by the worker. Streams are live —
          subscribe to one to watch the agent loop in real time.
        </p>
      </header>
      <RunList limit={40} />
    </div>
  );
}
