const PREFIX = "topmatch.apply.";

type ApplySession = {
  email: string;
};

export function saveApplySession(slug: string, email: string): void {
  if (typeof window === "undefined") {
    return;
  }
  window.sessionStorage.setItem(`${PREFIX}${slug}`, JSON.stringify({ email } satisfies ApplySession));
}

export function readApplySession(slug: string): ApplySession | null {
  if (typeof window === "undefined") {
    return null;
  }
  const raw = window.sessionStorage.getItem(`${PREFIX}${slug}`);
  if (!raw) {
    return null;
  }
  try {
    const parsed: unknown = JSON.parse(raw);
    if (
      parsed !== null &&
      typeof parsed === "object" &&
      "email" in parsed &&
      typeof parsed.email === "string" &&
      parsed.email
    ) {
      return { email: parsed.email };
    }
  } catch {
    return null;
  }
  return null;
}
