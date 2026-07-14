"use client";

import Box from "@mui/material/Box";
import Link from "@mui/material/Link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type LinkifiedTextProps = {
  text: string;
  /** Overrides the link color, e.g. "inherit" on colored chat bubbles. */
  linkColor?: string;
};

/** Renders untrusted backend text as Markdown without allowing raw HTML. */
export function LinkifiedText({ text, linkColor }: LinkifiedTextProps) {
  return (
    <Box
      sx={{
        overflowWrap: "anywhere",
        whiteSpace: "pre-wrap",
        "& > :first-child": { mt: 0 },
        "& > :last-child": { mb: 0 },
        "& p": { my: 1 },
        "& ul, & ol": { my: 1, pl: 3 },
        "& li": { my: 0.5 },
        "& li > p": { my: 0 },
        "& blockquote": {
          my: 1,
          mx: 0,
          pl: 1.5,
          borderLeft: 3,
          borderColor: "divider",
          color: "text.secondary",
        },
        "& code": {
          px: 0.5,
          py: 0.125,
          borderRadius: 0.5,
          bgcolor: "action.hover",
          fontFamily: "monospace",
          fontSize: "0.9em",
        },
        "& pre": { overflowX: "auto", my: 1 },
        "& pre code": { display: "block", p: 1 },
      }}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children, title }) => {
            const isExternal = href?.startsWith("http://") || href?.startsWith("https://");
            return (
              <Link
                href={href}
                title={title}
                {...(isExternal ? { target: "_blank", rel: "noopener noreferrer" } : {})}
                sx={linkColor ? { color: linkColor, textDecorationColor: "inherit" } : undefined}
              >
                {children}
              </Link>
            );
          },
        }}
      >
        {text}
      </ReactMarkdown>
    </Box>
  );
}
