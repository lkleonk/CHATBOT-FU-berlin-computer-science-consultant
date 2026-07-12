"use client";

import ArrowBackOutlinedIcon from "@mui/icons-material/ArrowBackOutlined";
import Box from "@mui/material/Box";
import Link from "@mui/material/Link";
import Typography from "@mui/material/Typography";
import { alpha } from "@mui/material/styles";
import NextLink from "next/link";
import type { ReactNode } from "react";

type LegalPageShellProps = {
  eyebrow: string;
  title: string;
  lead: string;
  children: ReactNode;
};

type LegalSectionProps = {
  title: string;
  children: ReactNode;
};

export function LegalPageShell({ eyebrow, title, lead, children }: LegalPageShellProps) {
  return (
    <Box
      component="main"
      lang="de"
      sx={{
        height: "100dvh",
        overflowY: "auto",
        bgcolor: "background.default",
        color: "text.primary",
        px: { xs: 2.5, sm: 4 },
        py: { xs: 4, sm: 6 },
      }}
    >
      <Box sx={{ width: "100%", maxWidth: 840, mx: "auto" }}>
        <Link
          component={NextLink}
          href="/consultant"
          underline="hover"
          sx={{ display: "inline-flex", alignItems: "center", gap: 0.75, mb: 4, fontSize: 14 }}
        >
          <ArrowBackOutlinedIcon sx={{ fontSize: 18 }} />
          Zurück zu Modulio
        </Link>

        <Typography
          component="p"
          sx={{
            m: 0,
            mb: 1,
            color: "text.secondary",
            fontSize: 13,
            fontWeight: 700,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
          }}
        >
          {eyebrow}
        </Typography>
        <Typography
          component="h1"
          sx={{
            m: 0,
            mb: 2,
            fontSize: "clamp(2rem, 6vw, 3.25rem)",
            fontWeight: 700,
            lineHeight: 1,
          }}
        >
          {title}
        </Typography>
        <Typography
          component="p"
          sx={{ maxWidth: 700, m: 0, mb: 4.5, color: "text.secondary", lineHeight: 1.7 }}
        >
          {lead}
        </Typography>

        {children}
      </Box>
    </Box>
  );
}

export function LegalSection({ title, children }: LegalSectionProps) {
  return (
    <Box
      component="section"
      sx={{
        py: 3.5,
        borderTop: 1,
        borderColor: "divider",
        "& h3": {
          mt: 2.75,
          mb: 1,
          fontSize: 16,
          lineHeight: 1.4,
        },
        "& p, & li, & address": {
          color: "text.secondary",
          fontSize: 14,
          lineHeight: 1.7,
        },
        "& p, & ul": { mt: 0, mb: 1.75 },
        "& ul": { pl: 2.5 },
        "& address": { fontStyle: "normal" },
        "& a": { color: "primary.main", textDecoration: "none" },
        "& a:hover": { textDecoration: "underline" },
        "& > :last-child": { mb: 0 },
      }}
    >
      <Typography component="h2" variant="h2" sx={{ m: 0, mb: 1.5 }}>
        {title}
      </Typography>
      {children}
    </Box>
  );
}

export function LegalConfigurationNotice() {
  return (
    <Box
      role="note"
      sx={{
        mb: 3,
        p: 2,
        border: 1,
        borderColor: "warning.main",
        borderRadius: 1,
        bgcolor: (theme) =>
          alpha(theme.palette.warning.main, theme.palette.mode === "dark" ? 0.12 : 0.08),
        color: "text.primary",
        fontSize: 14,
        lineHeight: 1.6,
      }}
    >
      Die Betreiberangaben sind noch nicht vollständig konfiguriert. Vor einer öffentlichen
      Bereitstellung müssen die Platzhalter über die <code>NEXT_PUBLIC_LEGAL_*</code>-Variablen
      durch echte Kontaktdaten ersetzt werden.
    </Box>
  );
}
