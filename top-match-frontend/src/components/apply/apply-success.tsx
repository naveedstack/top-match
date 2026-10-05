"use client";

import { useRouter } from "next/navigation";
import { useEffect, useSyncExternalStore } from "react";

import { Icon } from "@/components/icon";
import { applyPath } from "@/lib/apply-path";
import { readApplySession } from "@/lib/apply-session";

function subscribeApplySession() {
  return () => {};
}

export function ApplySuccess({ company, slug }: { company: string; slug: string }) {
  const router = useRouter();
  const email = useSyncExternalStore(
    subscribeApplySession,
    () => readApplySession(slug)?.email ?? null,
    () => null,
  );

  useEffect(() => {
    if (!readApplySession(slug)) {
      router.replace(applyPath(company, slug));
    }
  }, [company, router, slug]);

  if (!email) {
    return <p className="text-body-md text-on-surface-variant">Loading…</p>;
  }

  const session = readApplySession(slug);
  const title = session?.title;
  const privacyNotice = session?.privacyNotice;

  return (
    <main className="rounded-xl border border-outline-variant bg-surface-container-lowest p-6 shadow-sm md:p-10">
      <div className="flex flex-col items-center text-center">
        <div className="mb-5 flex size-16 items-center justify-center rounded-full border border-outline-variant bg-surface-container shadow-sm">
          <div className="flex size-11 items-center justify-center rounded-full bg-surface-container-high text-on-tertiary-container">
            <Icon className="text-[26px]" name="check" />
          </div>
        </div>
        <h1 className="mb-2 text-headline-lg tracking-tight text-on-surface md:text-headline-xl">
          Application Received
        </h1>
        <p className="max-w-lg text-body-md leading-relaxed text-on-surface-variant">
          Your application
          {title ? (
            <>
              {" "}
              for <span className="font-semibold text-on-surface">{title}</span>
            </>
          ) : null}{" "}
          has been submitted.
        </p>
      </div>

      <div className="mt-8 rounded-lg border border-outline-variant bg-surface p-5">
        <p className="mb-1 text-label-sm tracking-wider text-on-surface-variant uppercase">
          Applicant
        </p>
        <p className="text-label-lg font-medium text-on-surface">{email}</p>
      </div>

      {privacyNotice ? (
        <div className="mt-6 flex items-start gap-3 rounded-lg border border-outline-variant bg-surface p-3.5">
          <Icon className="mt-0.5 shrink-0 text-[20px] text-secondary" name="lock" />
          <p className="text-body-sm leading-relaxed text-on-surface-variant">{privacyNotice}</p>
        </div>
      ) : null}
    </main>
  );
}
