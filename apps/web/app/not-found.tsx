import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex flex-col items-start gap-6 py-16">
      <div className="text-eyebrow text-[color:var(--color-stone)]">404</div>
      <h1 className="text-display-lg text-[color:var(--color-charcoal)]">
        Nothing here.
      </h1>
      <p className="text-body-md text-[color:var(--color-slate)] max-w-[60ch]">
        The page you tried to open doesn&apos;t exist. Please verify the URL or navigate back to the dashboard.
      </p>
      <Link href="/">
        <Button variant="primary">Back to dashboard</Button>
      </Link>
    </div>
  );
}
