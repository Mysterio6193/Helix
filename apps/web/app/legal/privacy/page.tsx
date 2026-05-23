import { LegalShell, H2, P, UL } from "../legal-shell";

export const metadata = {
  title: "Privacy Policy · Helix",
  description: "How Helix collects, uses, and protects your information.",
};

export default function PrivacyPage() {
  return (
    <LegalShell
      eyebrow="Legal"
      title="Privacy policy."
      updated="May 15, 2026"
    >
      <P>
        This policy describes what information Helix collects when you use the
        product, why we collect it, and how it is protected. By using Helix,
        you agree to the practices described here.
      </P>

      <H2>1. Information we collect</H2>
      <P>
        We collect only the information needed to operate the product:
      </P>
      <UL>
        <li>
          <strong className="text-white">Account data</strong> — the email
          address and name you provide when you sign up, plus authentication
          metadata such as session tokens.
        </li>
        <li>
          <strong className="text-white">Workspace content</strong> — brand
          briefs, assets, workflow inputs, and run outputs you create inside
          the product.
        </li>
        <li>
          <strong className="text-white">Model credentials</strong> — provider
          keys you choose to connect (e.g. OpenAI, Anthropic). These are
          stored encrypted and never returned to the browser in plaintext.
        </li>
        <li>
          <strong className="text-white">Operational telemetry</strong> —
          request logs, error traces, and aggregate usage metrics required to
          keep the service running.
        </li>
      </UL>

      <H2>2. How we use information</H2>
      <UL>
        <li>To provide, maintain, and improve the Helix product.</li>
        <li>To authenticate you and protect your account.</li>
        <li>To execute workflows and deliver outputs you request.</li>
        <li>
          To respond to support requests and communicate operational changes.
        </li>
      </UL>
      <P>
        We do not sell your data, and we do not use your workspace content to
        train shared foundation models.
      </P>

      <H2>3. Model providers</H2>
      <P>
        When you run a workflow, the relevant prompt and inputs are sent to
        the model provider you configured (for example, OpenAI or Anthropic).
        Those providers operate under their own terms and privacy practices.
        We send only what is necessary to fulfill the request.
      </P>

      <H2>4. Data retention</H2>
      <P>
        Workspace content is retained for as long as your account is active.
        You can delete brands, runs, and assets from the product at any time.
        On account deletion, your workspace data is removed within thirty
        days, except where retention is required for security or legal
        reasons.
      </P>

      <H2>5. Security</H2>
      <P>
        We use industry-standard practices to protect data in transit and at
        rest. Workspace isolation is enforced at the data layer; provider
        credentials are stored in an encrypted vault. See{" "}
        <a href="/security" className="underline hover:text-white">
          /security
        </a>{" "}
        for the full posture.
      </P>

      <H2>6. Your rights</H2>
      <P>
        You can request access to, correction of, or deletion of personal data
        we hold about you. To make a request, contact us via the{" "}
        <a href="/contact" className="underline hover:text-white">
          contact form
        </a>
        .
      </P>

      <H2>7. Changes to this policy</H2>
      <P>
        We may update this policy as the product evolves. Material changes
        will be announced in-product or via email to the address on file.
      </P>

      <H2>8. Contact</H2>
      <P>
        For privacy questions, use the contact form. We answer from a real
        inbox, not a ticketing system.
      </P>
    </LegalShell>
  );
}
