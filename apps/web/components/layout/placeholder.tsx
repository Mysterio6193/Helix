import { Card, CardSubtitle, CardTitle } from "@/components/ui/card";

export function Placeholder({
  eyebrow,
  title,
  description,
  phase,
}: {
  eyebrow: string;
  title: string;
  description: string;
  phase: string;
}) {
  return (
    <div className="space-y-8">
      <header>
        <div className="text-eyebrow text-[color:var(--color-stone)]">{eyebrow}</div>
        <h1 className="text-display-lg text-[color:var(--color-charcoal)]">
          {title}
        </h1>
      </header>
      <Card feature>
        <CardTitle>Wired up in {phase}</CardTitle>
        <CardSubtitle>{description}</CardSubtitle>
      </Card>
    </div>
  );
}
