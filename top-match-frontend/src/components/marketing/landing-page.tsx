"use client";

import Link from "next/link";
import { useState } from "react";

import { Brand } from "@/components/brand";
import { Icon } from "@/components/icon";

const DEMO_HOSTED_PATH = "app.topmatch.example/soft-tech/WkAHIWFBCb8";
const DEMO_APPLY_URL = `https://${DEMO_HOSTED_PATH}`;

const NAV = [
  { href: "#how-it-works", label: "How it works" },
  { href: "#product", label: "Product" },
  { href: "#compliance", label: "Privacy & Compliance" },
] as const;

export function LandingPage() {
  return (
    <div className="min-h-screen bg-surface text-on-surface">
      <header className="sticky top-0 z-50 border-b border-outline-variant bg-surface-container-lowest/95 shadow-sm backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-[1440px] items-center justify-between px-space-lg md:px-margin">
          <Link className="flex items-center gap-space-sm" href="/">
            <Brand />
            <span className="hidden px-space-xs font-light text-outline-variant sm:inline-block">|</span>
            <span className="hidden text-label-sm tracking-wider text-on-surface-variant uppercase sm:inline-block">
              Screening Middleware
            </span>
          </Link>
          <nav className="hidden h-full items-center space-x-space-lg md:flex">
            {NAV.map((item) => (
              <a
                className="text-label-lg text-on-surface-variant transition-colors duration-150 hover:text-on-surface"
                href={item.href}
                key={item.href}
              >
                {item.label}
              </a>
            ))}
          </nav>
          <div className="flex items-center gap-space-sm">
            <Link
              className="rounded-lg border border-outline-variant bg-surface-container-lowest px-space-md py-1.5 text-label-md text-on-surface transition-colors duration-150 hover:border-outline hover:bg-surface-container-low"
              href="/login"
            >
              Log in
            </Link>
            <Link
              className="rounded-lg bg-primary px-space-md py-1.5 text-label-md text-on-primary shadow-sm transition-colors duration-150 hover:bg-primary-container"
              href="/register"
            >
              Create account
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1440px] space-y-24 px-space-lg py-12 md:px-margin md:py-16">
        <Hero />
        <Problem />
        <HowItWorks />
        <Product />
        <Compliance />
        <Boundary />
        <FinalCta />
      </main>

      <footer className="mt-16 border-t border-outline-variant bg-surface-container-lowest py-10">
        <div className="mx-auto flex max-w-[1440px] flex-col items-center justify-between gap-6 px-space-lg md:flex-row md:px-margin">
          <div className="flex items-center gap-space-sm">
            <Brand />
            <span className="text-outline-variant">·</span>
            <span className="text-label-sm text-on-surface-variant">AI resume-screening middleware</span>
          </div>
          <div className="flex flex-wrap items-center gap-space-lg text-label-md text-on-surface-variant">
            <a className="transition-colors duration-150 hover:text-on-surface" href="#how-it-works">
              How it works
            </a>
            <a className="transition-colors duration-150 hover:text-on-surface" href="#product">
              Product
            </a>
            <a className="transition-colors duration-150 hover:text-on-surface" href="#compliance">
              Privacy
            </a>
            <Link className="transition-colors duration-150 hover:text-on-surface" href="/login">
              Log in
            </Link>
            <Link className="transition-colors duration-150 hover:text-on-surface" href="/register">
              Register
            </Link>
          </div>
          <div className="text-label-sm text-outline">
            © 2026 Top Match Technologies, Inc. All rights reserved. Beta release.
          </div>
        </div>
      </footer>
    </div>
  );
}

function Hero() {
  return (
    <section className="grid grid-cols-1 items-center gap-gutter lg:grid-cols-12">
      <div className="space-y-6 lg:col-span-6">
        <div className="inline-flex items-center gap-space-xs rounded-full border border-outline-variant bg-surface-container px-3 py-1 text-label-sm text-secondary">
          <span className="size-1.5 rounded-full bg-secondary" />
          <span>AI resume-screening middleware · Not an ATS</span>
        </div>
        <h1 className="text-headline-xl font-bold tracking-tight text-on-surface md:text-[44px] md:leading-[52px]">
          Screen the flood.
          <br />
          Keep your ATS.
        </h1>
        <p className="max-w-xl text-body-lg text-on-surface-variant">
          Recruiters paste a hosted apply link on LinkedIn or Indeed. Candidates submit an email and
          PDF resume with zero account creation. Top Match ranks them against your rubric in real
          time.
        </p>
        <div className="flex flex-col items-stretch gap-space-sm pt-2 sm:flex-row sm:items-center">
          <Link
            className="inline-flex items-center justify-center gap-space-xs rounded-lg bg-primary px-5 py-3 text-label-lg text-on-primary shadow-sm transition-colors duration-150 hover:bg-primary-container"
            href="/register"
          >
            Create a free account
            <Icon className="text-[18px]" name="arrow_forward" />
          </Link>
          <Link
            className="inline-flex items-center justify-center rounded-lg border border-outline-variant bg-surface-container-lowest px-5 py-3 text-label-lg text-on-surface transition-colors duration-150 hover:border-outline hover:bg-surface-container-low"
            href="/login"
          >
            Log in
          </Link>
        </div>
        <div className="flex items-center gap-space-xs pt-1 text-label-sm text-on-surface-variant">
          <Icon className="text-[16px] text-secondary" name="verified_user" />
          <span>
            Beta release · No credit card required · Stays in front of Greenhouse, Lever, and
            Workday
          </span>
        </div>
      </div>
      <div className="lg:col-span-6">
        <PipelineMock />
      </div>
    </section>
  );
}

function PipelineMock() {
  const [copied, setCopied] = useState(false);

  async function copyDemoLink() {
    try {
      await navigator.clipboard.writeText(DEMO_APPLY_URL);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="overflow-hidden rounded-xl border border-outline-variant bg-surface-container-lowest shadow-sm">
      <div className="flex flex-col justify-between gap-space-sm border-b border-outline-variant bg-surface-container-low p-space-md sm:flex-row sm:items-center">
        <div className="flex items-center gap-space-sm overflow-hidden">
          <Icon className="shrink-0 text-[20px] text-secondary" name="link" />
          <span className="shrink-0 text-label-sm tracking-wider text-on-surface-variant uppercase">
            Hosted Link:
          </span>
          <code className="truncate rounded border border-outline-variant bg-surface-container-lowest px-2 py-0.5 text-label-sm text-on-surface">
            {DEMO_HOSTED_PATH}
          </code>
        </div>
        <button
          className="inline-flex shrink-0 items-center gap-1 text-label-sm text-secondary hover:underline"
          onClick={() => void copyDemoLink()}
          type="button"
        >
          <Icon className="text-[14px]" name={copied ? "check" : "content_copy"} />
          <span>{copied ? "Copied" : "Copy"}</span>
        </button>
      </div>
      <div className="border-b border-outline-variant p-space-md">
        <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
          <div>
            <span className="text-label-sm tracking-wider text-on-surface-variant uppercase">
              Live Pipeline
            </span>
            <h3 className="text-headline-sm font-semibold text-on-surface">
              Senior Backend Engineer (Distributed Systems)
            </h3>
          </div>
          <span className="inline-flex items-center gap-1.5 self-start rounded bg-secondary-fixed/50 px-2 py-1 text-label-sm text-secondary sm:self-auto">
            <span className="size-2 animate-pulse rounded-full bg-secondary" />
            <span>Active Rubric v2.4</span>
          </span>
        </div>
        <div className="mt-space-md grid grid-cols-2 gap-2 sm:grid-cols-4">
          <div className="rounded border border-outline-variant/50 bg-surface-container p-2">
            <div className="text-label-sm text-on-surface-variant">Received</div>
            <div className="text-headline-sm font-semibold text-on-surface">42</div>
          </div>
          <div className="flex items-center justify-between rounded border border-outline-variant/50 bg-surface-container p-2">
            <div>
              <div className="text-label-sm text-secondary">Processing</div>
              <div className="text-headline-sm font-semibold text-secondary">5</div>
            </div>
            <Icon className="animate-spin text-[16px] text-secondary" name="sync" />
          </div>
          <div className="rounded border border-outline-variant/50 bg-surface-container p-2">
            <div className="text-label-sm text-on-surface-variant">Scored</div>
            <div className="text-headline-sm font-semibold text-on-surface">128</div>
          </div>
          <div className="rounded border border-outline-variant/50 bg-surface-container p-2">
            <div className="text-label-sm text-error">Refused</div>
            <div className="text-headline-sm font-semibold text-error">14</div>
          </div>
        </div>
      </div>
      <div className="divide-y divide-outline-variant/60">
        <MockRow
          detail="Clean citation check · 6.5 yrs distributed systems"
          email="marcus.chen@example.com"
          icon="check_circle"
          rank="#1"
          score="94"
          when="Scored 4m ago"
        />
        <MockRow
          detail="Clean citation check · Kafka/Raft verified"
          email="priya.patel@cloudmail.io"
          icon="check_circle"
          rank="#2"
          score="88"
          when="Scored 11m ago"
        />
        <MockRow
          className="bg-error-container/10"
          detail="Citation mismatch · Golang claimed, no repos cited"
          detailClass="text-error"
          email="alex.vance@techcorp.net"
          icon="warning"
          rank="#3"
          score="81"
          when="Flagged"
        />
        <MockRow
          detail="Extracting system architecture evidence..."
          detailClass="text-secondary"
          email="samira.k@workmail.com"
          emailClass="font-medium"
          icon="progress_activity"
          iconClass="animate-spin"
          rank="#4"
          score="—"
          scoreClass="font-semibold text-outline"
          when="Processing"
          whenClass="text-secondary"
        />
      </div>
      <div className="flex items-center justify-between border-t border-outline-variant bg-surface-container-low px-space-md py-space-sm text-[11px] text-on-surface-variant">
        <span>Real-time polling: active</span>
        <span className="font-mono">Live Sync: 2s latency</span>
      </div>
    </div>
  );
}

function MockRow({
  rank,
  email,
  emailClass,
  detail,
  detailClass,
  icon,
  iconClass,
  score,
  scoreClass,
  when,
  whenClass,
  className,
}: {
  rank: string;
  email: string;
  emailClass?: string;
  detail: string;
  detailClass?: string;
  icon: string;
  iconClass?: string;
  score: string;
  scoreClass?: string;
  when: string;
  whenClass?: string;
  className?: string;
}) {
  return (
    <div
      className={`flex items-center justify-between p-space-md transition-colors duration-150 hover:bg-surface-container-low ${className ?? ""}`}
    >
      <div className="flex items-center gap-space-md">
        <span className="w-5 text-label-md text-on-surface-variant">{rank}</span>
        <div>
          <div className={`text-label-lg text-on-surface ${emailClass ?? "font-semibold"}`}>{email}</div>
          <div
            className={`mt-0.5 inline-flex items-center gap-1 text-[11px] font-medium ${detailClass ?? "text-on-tertiary-container"}`}
          >
            <Icon className={`text-[14px] ${iconClass ?? ""}`} name={icon} />
            <span>{detail}</span>
          </div>
        </div>
      </div>
      <div className="text-right">
        {score === "—" ? (
          <span className={`text-headline-sm ${scoreClass ?? "font-bold text-on-surface"}`}>{score}</span>
        ) : (
          <>
            <span className={`text-headline-sm ${scoreClass ?? "font-bold text-on-surface"}`}>{score}</span>
            <span className="text-label-sm text-on-surface-variant">/100</span>
          </>
        )}
        <span className={`block text-[11px] ${whenClass ?? "text-on-surface-variant"}`}>{when}</span>
      </div>
    </div>
  );
}

function Problem() {
  return (
    <section className="space-y-8">
      <div className="border-b border-outline-variant pb-4">
        <span className="text-label-sm font-semibold tracking-wider text-secondary uppercase">
          The Friction Point
        </span>
        <h2 className="mt-1 text-headline-lg font-semibold tracking-tight text-on-surface">
          Why traditional top-of-funnel recruiting breaks down
        </h2>
      </div>
      <div className="grid grid-cols-1 gap-gutter md:grid-cols-3">
        <ProblemCard
          footer="Problem: Signal-to-noise deficit"
          icon="inbox"
          text="Single-click applications flood recruiter queues with unqualified and non-compliant candidates, actively burying genuine talent under hundreds of automated submissions."
          title="Easy Apply dumps 500+ unvetted resumes"
        />
        <ProblemCard
          footer="Problem: Heavy architecture mismatch"
          icon="account_tree"
          text="Heavy enterprise systems like Greenhouse or Workday are engineered for post-screen workflow and compliance, not high-speed algorithmic top-of-funnel screening."
          title="Your ATS is where you hire, not where you filter"
        />
        <ProblemCard
          footer="Problem: Candidate attrition friction"
          icon="person_cancel"
          text="Forcing senior candidates to register an 8-page proprietary account produces massive drop-off rates. Top Match strips all friction down to clean email and PDF submission."
          title="Candidates refuse another portal account"
        />
      </div>
    </section>
  );
}

function ProblemCard({
  icon,
  title,
  text,
  footer,
}: {
  icon: string;
  title: string;
  text: string;
  footer: string;
}) {
  return (
    <div className="flex flex-col justify-between rounded-xl border border-outline-variant bg-surface-container-lowest p-space-lg shadow-sm">
      <div className="space-y-3">
        <div className="flex size-10 items-center justify-center rounded-lg bg-surface-container text-primary">
          <Icon name={icon} />
        </div>
        <h3 className="text-headline-sm font-semibold text-on-surface">{title}</h3>
        <p className="text-body-md text-on-surface-variant">{text}</p>
      </div>
      <div className="mt-4 border-t border-outline-variant/40 pt-6 text-label-sm text-outline">{footer}</div>
    </div>
  );
}

function HowItWorks() {
  return (
    <section className="space-y-10" id="how-it-works">
      <div className="mx-auto max-w-2xl space-y-2 text-center">
        <span className="text-label-sm font-semibold tracking-wider text-secondary uppercase">
          Operational Workflow
        </span>
        <h2 className="text-headline-lg font-semibold tracking-tight text-on-surface">
          How Top Match operates as your buffer
        </h2>
        <p className="text-body-md text-on-surface-variant">
          Deploy structured screening in minutes without replacing your existing hiring software.
        </p>
      </div>
      <div className="grid grid-cols-1 gap-gutter md:grid-cols-3">
        <div className="relative rounded-xl border border-outline-variant bg-surface-container-lowest p-space-lg shadow-sm">
          <div className="mb-space-md flex size-8 items-center justify-center rounded-full bg-primary text-label-md font-bold text-on-primary">
            1
          </div>
          <h3 className="mb-2 text-headline-sm font-semibold text-on-surface">Define the rubric & form</h3>
          <p className="mb-4 text-body-md text-on-surface-variant">
            Set must-haves in plain text. Candidate email, resume PDF, and AI consent are permanently
            locked; add optional custom recruiter questions if needed.
          </p>
          <div className="rounded-lg border border-outline-variant bg-surface-container-low p-3 font-mono text-[11px] text-on-surface-variant">
            Must-have: 5+ yrs Distributed Systems, Kubernetes, Go or Rust experience.
          </div>
        </div>
        <div className="relative rounded-xl border border-outline-variant bg-surface-container-lowest p-space-lg shadow-sm">
          <div className="mb-space-md flex size-8 items-center justify-center rounded-full bg-primary text-label-md font-bold text-on-primary">
            2
          </div>
          <h3 className="mb-2 text-headline-sm font-semibold text-on-surface">Paste the hosted apply link</h3>
          <p className="mb-4 text-body-md text-on-surface-variant">
            Use your company slug link on LinkedIn or Indeed instead of 1-click Easy Apply. Candidates
            upload their PDF resume in seconds without passwords.
          </p>
          <div className="truncate rounded-lg border border-outline-variant bg-surface-container-low p-3 font-mono text-[11px] text-secondary">
            {DEMO_APPLY_URL}
          </div>
        </div>
        <div className="relative rounded-xl border border-outline-variant bg-surface-container-lowest p-space-lg shadow-sm">
          <div className="mb-space-md flex size-8 items-center justify-center rounded-full bg-primary text-label-md font-bold text-on-primary">
            3
          </div>
          <h3 className="mb-2 text-headline-sm font-semibold text-on-surface">
            Watch the live leaderboard & export
          </h3>
          <p className="mb-4 text-body-md text-on-surface-variant">
            Gemini evaluates resumes strictly against rubric requirements, provides verbatim
            citations, and exports verified top candidates straight to CSV or ATS.
          </p>
          <div className="flex items-center justify-between rounded-lg border border-outline-variant bg-surface-container-low p-3 text-[11px] text-on-surface-variant">
            <span>Leaderboard sync: Active</span>
            <span className="font-semibold text-secondary">Export to CSV →</span>
          </div>
        </div>
      </div>
    </section>
  );
}

function Product() {
  return (
    <section className="space-y-16" id="product">
      <div className="border-b border-outline-variant pb-4">
        <span className="text-label-sm font-semibold tracking-wider text-secondary uppercase">
          Product Architecture
        </span>
        <h2 className="mt-1 text-headline-lg font-semibold tracking-tight text-on-surface">
          Designed for clinical precision and high-throughput evaluation
        </h2>
      </div>

      <div className="grid grid-cols-1 items-center gap-gutter lg:grid-cols-12">
        <div className="space-y-4 lg:col-span-5">
          <div className="inline-flex items-center gap-1 text-label-sm font-semibold tracking-wider text-secondary uppercase">
            <Icon className="text-[16px]" name="leaderboard" />
            <span>01 · Triage Intelligence</span>
          </div>
          <h3 className="text-headline-md font-semibold text-on-surface">
            Live ranked leaderboard with anomaly detection
          </h3>
          <p className="text-body-md text-on-surface-variant">
            Applications update in real time every 2 seconds without page refreshes. Track incoming
            resumes across 5 canonical states, spot prompt-injection attempts, and flag unverified
            citations before interviews happen.
          </p>
          <ul className="space-y-2 pt-2">
            <FeatureItem text="5 Canonical States: Received, Processing, Scored, Refused, Failed" />
            <FeatureItem text="Automated prompt-injection and adversarial PDF screening" />
          </ul>
        </div>
        <div className="lg:col-span-7">
          <div className="rounded-xl border border-outline-variant bg-surface-container-lowest p-space-md shadow-sm">
            <div className="mb-3 flex items-center justify-between border-b border-outline-variant pb-3">
              <div className="flex items-center gap-2">
                <span className="size-3 rounded-full bg-outline-variant" />
                <span className="size-3 rounded-full bg-outline-variant" />
                <span className="size-3 rounded-full bg-outline-variant" />
                <span className="ml-2 font-mono text-label-sm text-on-surface-variant">
                  leaderboard_view.tsx
                </span>
              </div>
              <span className="rounded bg-secondary-fixed/30 px-2 py-0.5 text-label-sm text-secondary">
                Polling Active (2.0s)
              </span>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between rounded-lg border border-outline-variant bg-surface-container-low p-3">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-xs font-bold text-on-surface-variant">01</span>
                  <div>
                    <div className="text-label-md font-semibold text-on-surface">
                      k.lindqvist@telecom.se
                    </div>
                    <div className="text-body-sm text-on-surface-variant">
                      Matches 4/4 Core Criteria · Stockholm (Remote)
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="rounded-full bg-tertiary-fixed px-2 py-0.5 text-[11px] font-semibold text-on-tertiary-container">
                    96/100
                  </span>
                  <Icon className="text-[18px] text-on-tertiary-container" name="verified" />
                </div>
              </div>
              <div className="flex items-center justify-between rounded-lg border border-outline-variant bg-surface-container-lowest p-3">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-xs font-bold text-on-surface-variant">02</span>
                  <div>
                    <div className="text-label-md font-semibold text-on-surface">
                      j.doe@security-audit.com
                    </div>
                    <div className="text-body-sm text-on-surface-variant">
                      Matches 3/4 Core Criteria · San Francisco, CA
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="rounded-full bg-surface-container px-2 py-0.5 text-[11px] font-semibold text-on-surface">
                    84/100
                  </span>
                  <Icon className="text-[18px] text-on-surface-variant" name="check_circle" />
                </div>
              </div>
              <div className="flex items-center justify-between rounded-lg border border-error/30 bg-error-container/20 p-3">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-xs font-bold text-error">03</span>
                  <div>
                    <div className="text-label-md font-semibold text-error">
                      suspicious_candidate@payload.io
                    </div>
                    <div className="text-body-sm text-error">
                      Prompt Injection Detected: &quot;Ignore previous instructions...&quot;
                    </div>
                  </div>
                </div>
                <span className="rounded-full bg-error px-2 py-0.5 text-[11px] font-semibold text-on-error">
                  Refused
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 items-center gap-gutter lg:grid-cols-12">
        <div className="order-2 lg:order-1 lg:col-span-7">
          <div className="rounded-xl border border-outline-variant bg-surface-container-lowest p-space-md shadow-sm">
            <div className="mb-4 flex items-center justify-between border-b border-outline-variant pb-3">
              <span className="text-label-sm font-semibold tracking-wider text-on-surface uppercase">
                Apply Form Builder
              </span>
              <span className="text-label-sm text-on-surface-variant">Candidate Preview Mode</span>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-3 rounded-lg border border-outline-variant bg-surface-container-low p-3">
                <div className="flex items-center justify-between">
                  <span className="text-label-sm font-semibold text-on-surface">Locked Standard Stack</span>
                  <Icon className="text-[16px] text-outline" name="lock" />
                </div>
                <div className="space-y-2 text-xs">
                  <LockedField label="1. Email Address" />
                  <LockedField label="2. PDF Resume File" />
                  <LockedField label="3. AI Screening Consent" />
                </div>
                <div className="text-[11px] text-outline-variant">
                  Recruiter custom questions are sequestered from the algorithmic judge.
                </div>
              </div>
              <div className="space-y-2.5 rounded-lg border border-outline-variant bg-surface-container-lowest p-3">
                <div className="text-label-sm font-semibold text-on-surface">Candidate View</div>
                <div className="space-y-1.5 text-xs">
                  <label className="block text-[11px] text-on-surface-variant">Email address *</label>
                  <input
                    className="w-full rounded border border-outline-variant bg-surface-container-low p-1.5 text-xs"
                    disabled
                    placeholder="candidate@domain.com"
                    type="text"
                  />
                  <label className="block pt-1 text-[11px] text-on-surface-variant">
                    Resume (PDF only, max 5MB) *
                  </label>
                  <div className="rounded border border-dashed border-outline-variant p-3 text-center text-[11px] text-outline-variant">
                    Drop resume PDF here
                  </div>
                  <div className="flex items-center gap-1.5 pt-1 text-[11px] text-on-surface-variant">
                    <input
                      checked
                      className="rounded border-outline-variant text-primary"
                      disabled
                      readOnly
                      type="checkbox"
                    />
                    <span>Consent to algorithmic evaluation</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="order-1 space-y-4 lg:order-2 lg:col-span-5">
          <div className="inline-flex items-center gap-1 text-label-sm font-semibold tracking-wider text-secondary uppercase">
            <Icon className="text-[16px]" name="dynamic_form" />
            <span>02 · Controlled Intake</span>
          </div>
          <h3 className="text-headline-md font-semibold text-on-surface">
            Hosted apply form with live recruiter preview
          </h3>
          <p className="text-body-md text-on-surface-variant">
            Never fight with form builders. Email, PDF resume, and consent are permanently locked
            for compliance. Add up to 20 custom recruiter questions that stay in your dossier and
            are never fed to the AI judge.
          </p>
          <ul className="space-y-2 pt-2">
            <FeatureItem text="Single-click candidate link without registration friction" />
            <FeatureItem text="Strict compliance isolation between screening and human questions" />
          </ul>
        </div>
      </div>

      <div className="grid grid-cols-1 items-center gap-gutter lg:grid-cols-12">
        <div className="space-y-4 lg:col-span-5">
          <div className="inline-flex items-center gap-1 text-label-sm font-semibold tracking-wider text-secondary uppercase">
            <Icon className="text-[16px]" name="find_in_page" />
            <span>03 · Defensive Auditability</span>
          </div>
          <h3 className="text-headline-md font-semibold text-on-surface">
            Application dossier with exact resume citations
          </h3>
          <p className="text-body-md text-on-surface-variant">
            Understand every score. Top Match extracts verbatim pull quotes mapped directly to page
            numbers and rubric criteria. AI serves strictly as an objective filtering aid; hiring
            remains 100% human-governed.
          </p>
          <ul className="space-y-2 pt-2">
            <FeatureItem text="Verbatim quote verification against parsed PDF documents" />
            <FeatureItem text="Zero hallucinated experience or ungrounded qualifications" />
          </ul>
        </div>
        <div className="lg:col-span-7">
          <div className="rounded-xl border border-outline-variant bg-surface-container-lowest p-space-md shadow-sm">
            <div className="mb-3 flex items-center justify-between border-b border-outline-variant pb-3">
              <div className="flex items-center gap-2">
                <span className="text-headline-sm font-semibold text-on-surface">
                  Candidate Dossier: Marcus Chen
                </span>
                <span className="rounded bg-surface-container px-2 py-0.5 font-mono text-label-sm text-on-surface">
                  ID: app_89f02
                </span>
              </div>
              <span className="text-headline-sm font-bold text-on-surface">
                94<span className="text-xs font-normal text-on-surface-variant">/100</span>
              </span>
            </div>
            <div className="space-y-3">
              <div className="rounded-lg border border-outline-variant bg-surface-container-low p-3">
                <div className="mb-1.5 flex items-center justify-between">
                  <span className="text-label-sm font-semibold text-on-surface">
                    Requirement: Distributed consensus (Raft/Paxos)
                  </span>
                  <span className="rounded bg-tertiary-fixed px-2 py-0.5 text-[11px] font-semibold text-on-tertiary-container">
                    Verified · Match
                  </span>
                </div>
                <blockquote className="my-1.5 border-l-2 border-secondary pl-2 text-xs text-on-surface-variant italic">
                  &quot;Architected a multi-region Raft consensus layer in Go handling 45k write
                  operations per second with zero-loss failover.&quot;
                </blockquote>
                <div className="font-mono text-[11px] text-outline">
                  Source: Resume_Marcus_Chen.pdf · Page 2, Paragraph 4
                </div>
              </div>
              <div className="rounded-lg border border-outline-variant bg-surface-container-lowest p-3">
                <div className="mb-1.5 flex items-center justify-between">
                  <span className="text-label-sm font-semibold text-on-surface">
                    Requirement: 5+ years Production Go
                  </span>
                  <span className="rounded bg-tertiary-fixed px-2 py-0.5 text-[11px] font-semibold text-on-tertiary-container">
                    Verified · Match
                  </span>
                </div>
                <blockquote className="my-1.5 border-l-2 border-secondary pl-2 text-xs text-on-surface-variant italic">
                  &quot;Senior Infrastructure Engineer (2018–Present): Core maintainer of our
                  proprietary Go RPC framework.&quot;
                </blockquote>
                <div className="font-mono text-[11px] text-outline">
                  Source: Resume_Marcus_Chen.pdf · Page 1, Section: Experience
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function LockedField({ label }: { label: string }) {
  return (
    <div className="flex items-center justify-between rounded border border-outline-variant bg-surface-container-lowest p-2 text-on-surface">
      <span>{label}</span>
      <span className="text-[10px] text-outline">Fixed</span>
    </div>
  );
}

function FeatureItem({ text }: { text: string }) {
  return (
    <li className="flex items-center gap-2 text-label-md text-on-surface">
      <Icon className="text-[16px] text-secondary" name="check_circle" />
      <span>{text}</span>
    </li>
  );
}

function Compliance() {
  return (
    <section className="space-y-8" id="compliance">
      <div className="border-b border-outline-variant pb-4">
        <span className="text-label-sm font-semibold tracking-wider text-secondary uppercase">
          Governance & Trust
        </span>
        <h2 className="mt-1 text-headline-lg font-semibold tracking-tight text-on-surface">
          Architected for strict enterprise compliance
        </h2>
      </div>
      <div className="grid grid-cols-1 gap-gutter md:grid-cols-2 lg:grid-cols-4">
        <ComplianceCard
          icon="no_accounts"
          text="Candidates submit once with email + PDF. No passwords, no credential retention, and no portal friction."
          title="Zero Candidate Accounts"
        />
        <ComplianceCard
          icon="auto_delete"
          text="Candidate PII, raw resumes, and extracted text are permanently deleted 30 days after the job is closed."
          title="Automated 30-Day Purge"
        />
        <ComplianceCard
          icon="policy"
          text="EEOC & NYC Local Law 144 compliant. Resumes scored strictly against posted job requirements without demographic inference."
          title="Algorithmic Transparency"
        />
        <ComplianceCard
          icon="domain_verification"
          text="Workspaces are strictly siloed. Cross-company URLs return generic 404s, guaranteeing zero leakage of organizational data."
          title="Tenant Isolation"
        />
      </div>
    </section>
  );
}

function ComplianceCard({ icon, title, text }: { icon: string; title: string; text: string }) {
  return (
    <div className="space-y-2 rounded-xl border border-outline-variant bg-surface-container-lowest p-space-md shadow-sm">
      <div className="mb-2 flex size-8 items-center justify-center rounded-lg bg-surface-container text-secondary">
        <Icon className="text-[20px]" name={icon} />
      </div>
      <h4 className="text-headline-sm font-semibold text-on-surface">{title}</h4>
      <p className="text-body-sm text-on-surface-variant">{text}</p>
    </div>
  );
}

function Boundary() {
  return (
    <section>
      <div className="mx-auto max-w-3xl space-y-2 rounded-xl border border-outline-variant bg-surface-container-low p-space-lg text-center">
        <div className="inline-flex items-center gap-1.5 text-label-sm font-semibold tracking-wider text-on-surface-variant uppercase">
          <Icon className="text-[16px]" name="info" />
          <span>Architectural Scope & Boundaries</span>
        </div>
        <p className="mx-auto max-w-xl text-headline-sm font-semibold text-on-surface">
          &quot;If you need a full ATS, stay on Greenhouse or Lever. Top Match is screening
          middleware that sits cleanly in front of them.&quot;
        </p>
        <p className="text-body-sm text-on-surface-variant">
          We handle the unvetted deluge of top-of-funnel applications so your core recruiting
          database only receives high-confidence candidates.
        </p>
      </div>
    </section>
  );
}

function FinalCta() {
  return (
    <section className="mx-auto max-w-4xl space-y-6 rounded-2xl border border-outline-variant bg-surface-container-lowest p-space-xl text-center shadow-sm">
      <div className="space-y-2">
        <span className="text-label-sm font-semibold tracking-wider text-secondary uppercase">
          Get Started Immediately
        </span>
        <h2 className="text-headline-xl font-bold tracking-tight text-on-surface">
          Create your first apply link.
        </h2>
        <p className="mx-auto max-w-lg text-body-lg text-on-surface-variant">
          Stop reviewing 600 generic resumes by hand. Set up your first screening rubric in 3
          minutes.
        </p>
      </div>
      <div className="flex flex-col items-center justify-center gap-space-sm pt-2 sm:flex-row">
        <Link
          className="inline-flex w-full items-center justify-center gap-space-xs rounded-lg bg-primary px-6 py-3 text-label-lg text-on-primary shadow-sm transition-colors duration-150 hover:bg-primary-container sm:w-auto"
          href="/register"
        >
          Create account
          <Icon className="text-[18px]" name="arrow_forward" />
        </Link>
        <Link
          className="inline-flex w-full items-center justify-center rounded-lg border border-outline-variant bg-surface-container-lowest px-6 py-3 text-label-lg text-on-surface transition-colors duration-150 hover:border-outline hover:bg-surface-container-low sm:w-auto"
          href="/login"
        >
          Log in
        </Link>
      </div>
      <div className="pt-2 text-[12px] text-outline">
        Beta release · Enterprise tenant provisioning available on request
      </div>
    </section>
  );
}
