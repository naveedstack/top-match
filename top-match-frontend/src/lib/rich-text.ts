const HTML_TAG = /<\/?[a-z][\s\S]*>/i;

export function looksLikeHtml(value: string): boolean {
  return HTML_TAG.test(value);
}

export function plainTextFromRichText(value: string): string {
  return value
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<\/p>/gi, "\n")
    .replace(/<[^>]+>/g, "")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&#39;/gi, "'")
    .replace(/&quot;/gi, '"')
    .replace(/\u00a0/g, " ")
    .trim();
}

export function richTextIsEmpty(value: string): boolean {
  return plainTextFromRichText(value).length === 0;
}

function escapeHtml(value: string): string {
  return value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

export function toEditorHtml(value: string): string {
  if (!value.trim()) {
    return "";
  }
  if (looksLikeHtml(value)) {
    return value;
  }
  return value
    .split(/\n{2,}/)
    .map((block) => `<p>${escapeHtml(block).replace(/\n/g, "<br>")}</p>`)
    .join("");
}
