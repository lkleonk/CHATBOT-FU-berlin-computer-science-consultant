"use client";

import Link from "@mui/material/Link";
import type { ReactNode } from "react";

// Matches Markdown links [label](https://...) first, bare http(s) URLs second.
const LINK_RE = /\[([^\]\n]+)\]\((https?:\/\/[^\s)]+)\)|https?:\/\/[^\s<>"')\]]+/g;

// Punctuation directly after a bare URL is almost always sentence punctuation.
const TRAILING_PUNCTUATION_RE = /[.,;:!?]+$/;

type LinkifiedTextProps = {
  text: string;
  /** Overrides the link color, e.g. "inherit" on colored chat bubbles. */
  linkColor?: string;
};

export function LinkifiedText({ text, linkColor }: LinkifiedTextProps) {
  const nodes: ReactNode[] = [];
  let lastIndex = 0;

  for (const match of text.matchAll(LINK_RE)) {
    const index = match.index ?? 0;
    if (index > lastIndex) {
      nodes.push(text.slice(lastIndex, index));
    }

    const label = match[1];
    const markdownUrl = match[2];
    if (label && markdownUrl) {
      nodes.push(
        <Link
          key={index}
          href={markdownUrl}
          target="_blank"
          rel="noopener noreferrer"
          sx={linkColor ? { color: linkColor, textDecorationColor: "inherit" } : undefined}
        >
          {label}
        </Link>,
      );
    } else {
      const trailing = match[0].match(TRAILING_PUNCTUATION_RE)?.[0] ?? "";
      const url = trailing ? match[0].slice(0, -trailing.length) : match[0];
      nodes.push(
        <Link
          key={index}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          sx={{ wordBreak: "break-all", ...(linkColor ? { color: linkColor, textDecorationColor: "inherit" } : {}) }}
        >
          {url}
        </Link>,
      );
      if (trailing) {
        nodes.push(trailing);
      }
    }

    lastIndex = index + match[0].length;
  }

  if (lastIndex < text.length) {
    nodes.push(text.slice(lastIndex));
  }

  return <>{nodes}</>;
}
