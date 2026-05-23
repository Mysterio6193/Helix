import { LegalShell, H2, P, UL } from "../legal-shell";

export const metadata = {
  title: "Terms of Service · Helix",
  description: "The terms that govern your use of Helix.",
};

export default function TermsPage() {
  return (
    <LegalShell eyebrow="Legal" title="Terms of service." updated="May 15, 2026">
      <P>
        These terms govern your access to and use of Helix. By creating an
        account or using the product, you agree to them. If you are using
        Helix on behalf of an organization, you confirm that you have the
        authority to bind that organization to these terms.
      </P>

      <H2>1. Your account</H2>
      <UL>
        <li>You must provide accurate information when creating an account.</li>
        <li>
          You are responsible for activity that occurs under your credentials.
        </li>
        <li>
          You must keep your account secure and notify us promptly of any
          unauthorized use.
        </li>
      </UL>

      <H2>2. Acceptable use</H2>
      <P>You agree not to:</P>
      <UL>
        <li>
          Use Helix to generate, host, or distribute unlawful, infringing, or
          deceptive content.
        </li>
        <li>
          Attempt to bypass workspace isolation, scrape data belonging to
          other customers, or interfere with the operation of the service.
        </li>
        <li>
          Reverse-engineer the product for the purpose of building a
          competing service.
        </li>
        <li>
          Use the product to send unsolicited bulk communication, malware, or
          content that targets minors.
        </li>
      </UL>

      <H2>3. Your content</H2>
      <P>
        You retain ownership of brands, briefs, assets, and outputs you
        create with Helix. You grant us a limited license to process that
        content solely to operate the product on your behalf — for example,
        to run a workflow you triggered or to render an asset you uploaded.
      </P>

      <H2>4. Third-party model providers</H2>
      <P>
        Helix lets you connect external model providers using your own keys.
        Those providers operate under their own terms. We are not responsible
        for their outputs, availability, or pricing.
      </P>

      <H2>5. Subscriptions and billing</H2>
      <UL>
        <li>
          Paid plans are billed through Stripe on a recurring basis until
          cancelled.
        </li>
        <li>
          You can cancel from the billing surface inside the product;
          cancellation takes effect at the end of the current billing period.
        </li>
        <li>
          Fees already paid are non-refundable except where required by law.
        </li>
      </UL>

      <H2>6. Availability</H2>
      <P>
        We work to keep Helix available and reliable, but we do not guarantee
        uninterrupted service. Maintenance, third-party outages, and
        unexpected incidents can affect availability.
      </P>

      <H2>7. Termination</H2>
      <P>
        You can stop using Helix and delete your account at any time. We may
        suspend or terminate accounts that materially violate these terms,
        with notice where practical.
      </P>

      <H2>8. Disclaimers</H2>
      <P>
        Helix is provided on an &quot;as is&quot; basis. To the maximum
        extent permitted by law, we disclaim implied warranties of
        merchantability, fitness for a particular purpose, and
        non-infringement. AI-generated outputs may contain inaccuracies — you
        are responsible for reviewing them before use.
      </P>

      <H2>9. Limitation of liability</H2>
      <P>
        To the maximum extent permitted by law, our aggregate liability for
        any claim arising out of or relating to these terms is limited to the
        fees you paid us in the twelve months preceding the claim.
      </P>

      <H2>10. Changes</H2>
      <P>
        We may update these terms as the product evolves. Material changes
        will be announced in-product or via email. Continued use after the
        effective date constitutes acceptance.
      </P>

      <H2>11. Contact</H2>
      <P>
        Questions about these terms? Reach us through the{" "}
        <a href="/contact" className="underline hover:text-white">
          contact form
        </a>
        .
      </P>
    </LegalShell>
  );
}
