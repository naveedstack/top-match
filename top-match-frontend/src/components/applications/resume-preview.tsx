"use client";

import { useEffect, useRef, useState } from "react";

import { Icon } from "@/components/icon";
import { Button } from "@/components/ui/button";
import { fetchResumePdf, ResumeTokenExpiredError } from "@/lib/resume-pdf";

type ResumePreviewProps = {
  resumeUrl: string;
  onRefreshUrl: () => Promise<string | null>;
};

export function ResumePreview({ resumeUrl, onRefreshUrl }: ResumePreviewProps) {
  const [src, setSrc] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(true);
  const objectUrlRef = useRef<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load(url: string, allowRetry: boolean) {
      setPending(true);
      setError("");
      try {
        const blob = await fetchResumePdf(url);
        if (cancelled) {
          return;
        }
        if (objectUrlRef.current) {
          URL.revokeObjectURL(objectUrlRef.current);
        }
        objectUrlRef.current = URL.createObjectURL(blob);
        setSrc(objectUrlRef.current);
      } catch (caught) {
        if (cancelled) {
          return;
        }
        if (caught instanceof ResumeTokenExpiredError && allowRetry) {
          const next = await onRefreshUrl();
          if (next && !cancelled) {
            await load(next, false);
            return;
          }
        }
        setError("Could not load resume.");
      } finally {
        if (!cancelled) {
          setPending(false);
        }
      }
    }

    void load(resumeUrl, true);

    return () => {
      cancelled = true;
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }
    };
    // Parent remounts with key={application.id}. Ignore later resume_url tokens from polling.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- load once per application
  }, []);

  function openInNewTab() {
    if (src) {
      window.open(src, "_blank", "noopener,noreferrer");
    }
  }

  return (
    <div
      className="flex min-h-[560px] flex-col overflow-hidden rounded-xl border border-outline-variant bg-surface-container-lowest shadow-sm"
      id="pdf-preview"
    >
      <div className="flex items-center justify-between border-b border-outline-variant bg-surface-container px-space-md py-2.5">
        <div className="flex items-center gap-2">
          <Icon className="text-error" name="picture_as_pdf" />
          <span className="text-label-md font-semibold text-on-surface">Resume PDF</span>
        </div>
        <Button
          className="px-2.5 py-1 text-label-sm"
          disabled={!src}
          onClick={openInNewTab}
          type="button"
          variant="outline"
        >
          <Icon className="text-[16px]" name="open_in_new" />
          Open in new tab
        </Button>
      </div>
      {pending && !src ? (
        <p className="p-space-md text-body-md text-on-surface-variant">Loading resume…</p>
      ) : error && !src ? (
        <p className="p-space-md text-body-md text-error">{error}</p>
      ) : src ? (
        <iframe className="min-h-[560px] w-full flex-1 bg-surface-dim/40" src={src} title="Resume PDF" />
      ) : null}
    </div>
  );
}
