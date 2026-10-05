const PREFIX = "topmatch.apply.";

type ApplySession = {
  email: string;
  title?: string;
  privacyNotice?: string;
};

export function saveApplySession(
  slug: string,
  email: string,
  details?: { title?: string; privacyNotice?: string },
): void {
  if (typeof window === "undefined") {
    return;
  }
  const payload: ApplySession = { email };
  if (details?.title) {
    payload.title = details.title;
  }
  if (details?.privacyNotice) {
    payload.privacyNotice = details.privacyNotice;
  }
  window.sessionStorage.setItem(`${PREFIX}${slug}`, JSON.stringify(payload));
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
      const title =
        "title" in parsed && typeof parsed.title === "string" && parsed.title
          ? parsed.title
          : undefined;
      const privacyNotice =
        "privacyNotice" in parsed &&
        typeof parsed.privacyNotice === "string" &&
        parsed.privacyNotice
          ? parsed.privacyNotice
          : undefined;
      return { email: parsed.email, title, privacyNotice };
    }
  } catch {
    return null;
  }
  return null;
}
