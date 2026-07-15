"use client";

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import LaunchOutlinedIcon from "@mui/icons-material/LaunchOutlined";
import RefreshOutlinedIcon from "@mui/icons-material/RefreshOutlined";
import SportsEsportsOutlinedIcon from "@mui/icons-material/SportsEsportsOutlined";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useCallback, useEffect, useState } from "react";

import { useDegree } from "@/context/DegreeContext";
import { getProgramRules } from "@/services/api";
import type { ProgramRuleItem, ProgramRulesCatalogue } from "@/types/api";

import { LinkifiedText } from "./LinkifiedText";

const MODULIO_ESCAPE_URL = "https://degree-escape-room.vercel.app/";

function itemRange(item: ProgramRuleItem) {
  if (item.minimum !== null && item.maximum !== null && item.minimum === item.maximum) {
    return `${item.minimum} ${item.unit ?? ""}`.trim();
  }
  if (item.minimum !== null && item.maximum !== null) {
    return `${item.minimum}-${item.maximum} ${item.unit ?? ""}`.trim();
  }
  if (item.minimum !== null) {
    return `min ${item.minimum} ${item.unit ?? ""}`.trim();
  }
  if (item.maximum !== null) {
    return `max ${item.maximum} ${item.unit ?? ""}`.trim();
  }
  return null;
}

export function DegreeRulesTab() {
  const { effectiveDegreeId } = useDegree();
  const [catalogue, setCatalogue] = useState<ProgramRulesCatalogue | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadRules = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setCatalogue(await getProgramRules(effectiveDegreeId));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load degree rules.");
    } finally {
      setIsLoading(false);
    }
  }, [effectiveDegreeId]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadRules();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadRules]);

  return (
    <Box sx={{ height: "100%", overflowY: "auto", px: { xs: 1.5, md: 3 }, py: 2 }}>
        <Stack spacing={2} sx={{ maxWidth: 1100, mx: "auto" }}>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={1}
          sx={{
            alignItems: { xs: "flex-start", sm: "center" },
            justifyContent: "space-between",
          }}
        >
          <Box>
            <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }}>
              <Typography variant="h2">Degree Rules</Typography>
              {catalogue && (
                <Chip label={catalogue.catalogue_version} size="small" variant="outlined" />
              )}
            </Stack>
            {catalogue && (
              <Typography variant="body2" sx={{ color: "text.secondary", mt: 0.5 }}>
                {catalogue.degree_program} - {catalogue.regulation}
              </Typography>
            )}
            {catalogue && (
              <Typography
                variant="caption"
                sx={{ color: "text.secondary", display: "block", mt: 0.5 }}
              >
                {catalogue.source_note}
              </Typography>
            )}
          </Box>
          <Button startIcon={<RefreshOutlinedIcon />} onClick={() => void loadRules()}>
            Refresh
          </Button>
          </Stack>

          <Box
            component="section"
            aria-label="Degree escape room"
            sx={{
              display: "flex",
              flexWrap: "wrap",
              alignItems: "center",
              gap: 1,
              px: 1.5,
              py: 0.75,
              border: 1,
              borderColor: "divider",
              borderRadius: 2,
              bgcolor: "background.paper",
            }}
          >
            <SportsEsportsOutlinedIcon color="primary" fontSize="small" />
            <Typography variant="body2" sx={{ flexGrow: 1, color: "text.secondary" }}>
              Learn the degree through play in Modulio&apos;s external escape room.
            </Typography>
            <Button
              size="small"
              variant="outlined"
              endIcon={<LaunchOutlinedIcon />}
              href={MODULIO_ESCAPE_URL}
              target="_blank"
              rel="noopener noreferrer"
              sx={{ flexShrink: 0 }}
            >
              Play the escape room
            </Button>
          </Box>

          {isLoading && (
          <Stack direction="row" spacing={1} sx={{ alignItems: "center", color: "text.secondary" }}>
            <CircularProgress size={18} />
            <Typography variant="body2">Loading degree rules</Typography>
          </Stack>
        )}

        {error && <Alert severity="error">{error}</Alert>}

        {catalogue && (
          <Stack spacing={1}>
            {catalogue.sections.map((section) => (
              <Accordion key={section.id} disableGutters variant="outlined">
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box>
                    <Typography variant="h3">{section.title}</Typography>
                    <Typography variant="body2" sx={{ color: "text.secondary", mt: 0.5 }}>
                      {section.description}
                    </Typography>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Stack spacing={1.5}>
                    {section.items.map((item) => {
                      const range = itemRange(item);
                      return (
                        <Box
                          key={`${section.id}-${item.label}`}
                          sx={{
                            borderTop: 1,
                            borderColor: "divider",
                            pt: 1.25,
                          }}
                        >
                          <Stack
                            direction={{ xs: "column", sm: "row" }}
                            spacing={1}
                            sx={{
                              alignItems: { xs: "flex-start", sm: "center" },
                              justifyContent: "space-between",
                            }}
                          >
                            <Typography variant="body1" sx={{ fontWeight: 700 }}>
                              {item.label}
                            </Typography>
                            {range && <Chip label={range} size="small" variant="outlined" />}
                          </Stack>
                          <Box sx={{ typography: "body2", color: "text.secondary", mt: 0.5 }}>
                            <LinkifiedText text={item.text} />
                          </Box>
                        </Box>
                      );
                    })}

                    {section.sources.length > 0 && (
                      <Stack direction="row" spacing={0.75} sx={{ flexWrap: "wrap" }}>
                        {section.sources.map((source) => (
                          <Chip
                            key={`${section.id}-${source.label}`}
                            label={source.label}
                            size="small"
                            variant="outlined"
                            {...(source.path.startsWith("http")
                              ? {
                                  component: "a",
                                  href: source.path,
                                  target: "_blank",
                                  rel: "noreferrer",
                                  clickable: true,
                                }
                              : {})}
                          />
                        ))}
                      </Stack>
                    )}

                    {section.related_issue_codes.length > 0 && (
                      <Stack direction="row" spacing={0.75} sx={{ flexWrap: "wrap" }}>
                        {section.related_issue_codes.map((code) => (
                          <Chip key={`${section.id}-${code}`} label={code} size="small" />
                        ))}
                      </Stack>
                    )}
                  </Stack>
                </AccordionDetails>
              </Accordion>
            ))}
          </Stack>
        )}
      </Stack>
    </Box>
  );
}
