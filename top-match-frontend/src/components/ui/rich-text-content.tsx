"use client";

import { useEffect, useState } from "react";
import DOMPurify from "dompurify";

import { cn } from "@/lib/cn";
import { looksLikeHtml, plainTextFromRichText } from "@/lib/rich-text";

const ALLOWED_TAGS = ["p", "br", "strong", "em", "b", "i", "ul", "ol", "li", "h2", "h3", "blockquote"];

type RichTextContentProps = {
  html: string;
  className?: string;
};

export function RichTextContent({ html, className }: RichTextContentProps) {
  const [markup, setMarkup] = useState<string | null>(null);

  useEffect(() => {
    if (!looksLikeHtml(html)) {
      return;
    }
    setMarkup(
      DOMPurify.sanitize(html, {
        ALLOWED_TAGS,
        ALLOWED_ATTR: [],
      }),
    );
  }, [html]);

  if (!looksLikeHtml(html) || markup === null) {
    return (
      <p className={cn("whitespace-pre-wrap break-words", className)}>
        {looksLikeHtml(html) ? plainTextFromRichText(html) : html}
      </p>
    );
  }

  return (
    <div
      className={cn("rich-text break-words", className)}
      dangerouslySetInnerHTML={{ __html: markup }}
    />
  );
}
