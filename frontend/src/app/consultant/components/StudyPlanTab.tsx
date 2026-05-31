"use client";

import PrintOutlinedIcon from "@mui/icons-material/PrintOutlined";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import GlobalStyles from "@mui/material/GlobalStyles";
import Paper from "@mui/material/Paper";
import Snackbar from "@mui/material/Snackbar";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useCallback, useEffect, useState } from "react";

import { createSession } from "@/services/api";
import type {
  ModuleArea,
  PlannedModule,
  RuleCheckResult,
  StudyPlan,
  TranscriptUploadResponse,
} from "@/types/api";

import {
  appendStoredChatMessages,
  buildTranscriptChatMessages,
} from "./chatMessages";
import { RuleCheckPanel } from "./RuleCheckPanel";
import { SESSION_ID_STORAGE_KEY } from "./storage";
import { TranscriptUpload } from "./TranscriptUpload";

type StudyPlanTabProps = {
  latestRuleCheck: RuleCheckResult | null;
  latestStudyPlan: StudyPlan | null;
  sessionId: string | null;
  onSessionIdChange: (sessionId: string | null) => void;
  onRuleCheckResult: (result: RuleCheckResult | null) => void;
  onStudyPlan: (plan: StudyPlan | null) => void;
};

type AreaCardSpec = {
  id: ModuleArea | "wahlbereich";
  title: string;
  predicate: (module: PlannedModule) => boolean;
  emptyHint: string;
};

const AREA_CARDS: AreaCardSpec[] = [
  {
    id: "practical",
    title: "Praktische Informatik",
    predicate: (m) => m.area === "practical" && !m.is_wahlbereich,
    emptyHint: "No modules placed here yet.",
  },
  {
    id: "theoretical",
    title: "Theoretische Informatik",
    predicate: (m) => m.area === "theoretical" && !m.is_wahlbereich,
    emptyHint: "No modules placed here yet.",
  },
  {
    id: "technical",
    title: "Technische Informatik",
    predicate: (m) => m.area === "technical" && !m.is_wahlbereich,
    emptyHint: "No modules placed here yet.",
  },
  {
    id: "application",
    title: "Anwendungsbereich",
    predicate: (m) => m.area === "application" && !m.is_wahlbereich,
    emptyHint: "No application-area modules yet.",
  },
  {
    id: "wahlbereich",
    title: "Wahlbereich",
    predicate: (m) => m.is_wahlbereich,
    emptyHint: "No Wahlbereich modules yet.",
  },
  {
    id: "thesis",
    title: "Masterarbeit",
    predicate: (m) => m.area === "thesis",
    emptyHint: "No thesis module planned yet.",
  },
  {
    id: "unknown",
    title: "Unassigned",
    predicate: (m) => m.area === "unknown" && !m.is_wahlbereich,
    emptyHint: "All modules have an area.",
  },
];

const SPECIALIZATION_LABEL: Record<string, string> = {
  practical: "Praktische Informatik",
  theoretical: "Theoretische Informatik",
  technical: "Technische Informatik",
};

const PRINT_STYLES = {
  "@media print": {
    "@page": {
      margin: "14mm",
      size: "A4",
    },
    "html, body": {
      height: "auto !important",
      maxWidth: "none !important",
      overflow: "visible !important",
      background: "#ffffff !important",
    },
    '[data-print-hidden="true"]': {
      display: "none !important",
    },
    '[data-print-only="true"]': {
      display: "block !important",
    },
    "main, [role='tabpanel']": {
      height: "auto !important",
      minHeight: "0 !important",
      overflow: "visible !important",
    },
    '[data-study-plan-print-root="true"]': {
      height: "auto !important",
      overflow: "visible !important",
      padding: "0 !important",
      color: "#17211e !important",
      background: "#ffffff !important",
      WebkitPrintColorAdjust: "exact",
      printColorAdjust: "exact",
    },
    '[data-study-plan-print-report="true"]': {
      maxWidth: "none !important",
      margin: "0 !important",
    },
    '[data-study-plan-grid="true"]': {
      display: "grid !important",
      gridTemplateColumns: "repeat(2, minmax(0, 1fr)) !important",
      gap: "10px !important",
    },
    '[data-study-plan-print-root="true"] .MuiPaper-root': {
      breakInside: "avoid",
      pageBreakInside: "avoid",
      background: "#ffffff !important",
      borderColor: "#b8c7c1 !important",
      color: "#17211e !important",
      boxShadow: "none !important",
    },
    '[data-study-plan-print-root="true"] .MuiTypography-root': {
      color: "inherit !important",
    },
    '[data-study-plan-print-root="true"] .MuiChip-root': {
      backgroundColor: "#eef4f1 !important",
      borderColor: "#b8c7c1 !important",
      color: "#17211e !important",
    },
    '[data-study-plan-print-root="true"] .MuiChip-colorPrimary': {
      backgroundColor: "#d7efe6 !important",
      color: "#0b4d3a !important",
    },
    '[data-study-plan-print-root="true"] .MuiChip-colorSecondary': {
      backgroundColor: "#e4eefc !important",
      color: "#1c477a !important",
    },
    '[data-study-plan-print-root="true"] .MuiChip-colorSuccess': {
      backgroundColor: "#def7ec !important",
      color: "#03543f !important",
    },
    '[data-study-plan-print-root="true"] .MuiChip-colorWarning': {
      backgroundColor: "#fef3c7 !important",
      color: "#92400e !important",
    },
    '[data-study-plan-print-root="true"] .MuiChip-colorError': {
      backgroundColor: "#fde8e8 !important",
      color: "#9b1c1c !important",
    },
    '[data-study-plan-print-root="true"] .MuiAlert-root': {
      backgroundColor: "#ffffff !important",
      color: "#17211e !important",
    },
  },
};

function sumLp(modules: PlannedModule[]): number {
  return modules.reduce((total, module) => total + (module.lp || 0), 0);
}

function formatGeneratedAt(): string {
  return new Intl.DateTimeFormat("de-DE", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date());
}

function ModuleRow({ module }: { module: PlannedModule }) {
  const flags: string[] = [];
  if (module.is_scientific_work) flags.push("Wiss. Arbeiten");
  if (module.is_software_project) flags.push("Softwareprojekt");
  if (module.is_ungraded) flags.push("unbenotet");
  if (module.is_bachelor_module) flags.push("Bachelor");

  return (
    <Stack
      direction="row"
      spacing={1}
      sx={{
        alignItems: "center",
        justifyContent: "space-between",
        py: 0.5,
      }}
    >
      <Box sx={{ minWidth: 0 }}>
        <Typography variant="body2" sx={{ fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis" }}>
          {module.name}
        </Typography>
        {flags.length > 0 && (
          <Stack direction="row" spacing={0.5} sx={{ flexWrap: "wrap", mt: 0.25 }}>
            {flags.map((flag) => (
              <Chip key={flag} label={flag} size="small" variant="outlined" />
            ))}
          </Stack>
        )}
      </Box>
      <Chip label={`${module.lp} LP`} size="small" />
    </Stack>
  );
}

function AreaCard({
  title,
  modules,
  emptyHint,
}: {
  title: string;
  modules: PlannedModule[];
  emptyHint: string;
}) {
  const total = sumLp(modules);
  return (
    <Paper
      variant="outlined"
      sx={{
        p: 1.75,
        bgcolor: "background.paper",
        height: "100%",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Stack direction="row" spacing={1} sx={{ alignItems: "center", justifyContent: "space-between", mb: 1 }}>
        <Typography variant="h3">{title}</Typography>
        <Chip label={`${total} LP`} color={total > 0 ? "primary" : "default"} size="small" />
      </Stack>
      <Divider sx={{ mb: 1 }} />
      {modules.length === 0 ? (
        <Typography variant="body2" sx={{ color: "text.secondary", fontStyle: "italic" }}>
          {emptyHint}
        </Typography>
      ) : (
        <Stack divider={<Divider flexItem />} sx={{ flex: 1 }}>
          {modules.map((module, index) => (
            <ModuleRow key={`${module.name}-${index}`} module={module} />
          ))}
        </Stack>
      )}
    </Paper>
  );
}

export function StudyPlanTab({
  latestRuleCheck,
  latestStudyPlan,
  sessionId,
  onSessionIdChange,
  onRuleCheckResult,
  onStudyPlan,
}: StudyPlanTabProps) {
  const [generatedAt, setGeneratedAt] = useState(() => formatGeneratedAt());
  const [uploadError, setUploadError] = useState<string | null>(null);
  const modules = latestStudyPlan?.modules ?? [];
  const specialization = latestStudyPlan?.specialization_area ?? null;
  const totalLp = sumLp(modules);
  const scientificCount = modules.filter((m) => m.is_scientific_work).length;
  const softwareProjectCount = modules.filter((m) => m.is_software_project).length;
  const ungradedLp = sumLp(modules.filter((m) => m.is_ungraded));
  const bachelorLp = sumLp(modules.filter((m) => m.is_bachelor_module));

  useEffect(() => {
    const updateGeneratedAt = () => setGeneratedAt(formatGeneratedAt());
    window.addEventListener("beforeprint", updateGeneratedAt);

    return () => window.removeEventListener("beforeprint", updateGeneratedAt);
  }, []);

  const handlePrint = () => {
    setGeneratedAt(formatGeneratedAt());
    window.setTimeout(() => window.print(), 0);
  };

  const ensureSession = useCallback(async () => {
    if (sessionId) {
      return sessionId;
    }
    const created = await createSession();
    onSessionIdChange(created.session_id);
    window.sessionStorage.setItem(SESSION_ID_STORAGE_KEY, created.session_id);
    return created.session_id;
  }, [onSessionIdChange, sessionId]);

  // The Chat tab is unmounted while this tab is active, so persist the upload to
  // the shared chat store and lift state up. The Chat tab rehydrates from storage
  // when the user switches back.
  const handleTranscriptUploaded = useCallback(
    (result: TranscriptUploadResponse) => {
      setUploadError(null);
      appendStoredChatMessages(buildTranscriptChatMessages(result));
      onRuleCheckResult(result.rule_check_result);
      if (result.parsed_study_plan) {
        onStudyPlan(result.parsed_study_plan);
      }
    },
    [onRuleCheckResult, onStudyPlan],
  );

  return (
    <Box
      data-study-plan-print-root="true"
      sx={{ height: "100%", overflowY: "auto", px: { xs: 1.5, md: 3 }, py: 2 }}
    >
      <GlobalStyles styles={PRINT_STYLES} />
      <Stack data-study-plan-print-report="true" spacing={2} sx={{ maxWidth: 1100, mx: "auto" }}>
        <Box data-print-only="true" sx={{ display: "none", mb: 1 }}>
          <Typography variant="h1">FU Berlin CS Consultant</Typography>
          <Typography variant="body2" sx={{ color: "text.secondary" }}>
            Master Informatik study plan report - Generated {generatedAt}
          </Typography>
        </Box>

        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={1.5}
          sx={{ alignItems: { xs: "stretch", sm: "flex-start" }, justifyContent: "space-between" }}
        >
          <Box>
            <Typography variant="h2" sx={{ mb: 0.75 }}>
              Study Plan
            </Typography>
            <Typography variant="body2" sx={{ color: "text.secondary" }}>
              {latestStudyPlan
                ? "Latest extracted plan from your chat messages."
                : "Paste your modules into the Chat tab to extract a plan."}
            </Typography>
          </Box>
          <Stack
            direction="row"
            spacing={1}
            data-print-hidden="true"
            sx={{ alignSelf: { xs: "flex-start", sm: "center" }, flexShrink: 0 }}
          >
            <TranscriptUpload
              ensureSession={ensureSession}
              onUploaded={handleTranscriptUploaded}
              onError={setUploadError}
              variant="button"
            />
            {latestStudyPlan && (
              <Button
                variant="outlined"
                startIcon={<PrintOutlinedIcon />}
                onClick={handlePrint}
              >
                Save as PDF
              </Button>
            )}
          </Stack>
        </Stack>

        {latestStudyPlan && (
          <Paper variant="outlined" sx={{ p: 1.5, bgcolor: "background.paper" }}>
            <Stack direction="row" spacing={0.75} sx={{ flexWrap: "wrap" }}>
              <Chip label={`Total: ${totalLp} LP`} color="primary" />
              <Chip
                label={
                  specialization
                    ? `Vertiefung: ${SPECIALIZATION_LABEL[specialization] ?? specialization}`
                    : "Vertiefung: not set"
                }
                color={specialization ? "secondary" : "default"}
              />
              <Chip label={`Wiss. Arbeiten: ${scientificCount}`} />
              <Chip label={`Softwareprojekt: ${softwareProjectCount}`} />
              <Chip label={`Unbenotet: ${ungradedLp} LP`} />
              <Chip label={`Bachelor: ${bachelorLp} LP`} />
            </Stack>
          </Paper>
        )}

        {latestStudyPlan ? (
          <Box
            data-study-plan-grid="true"
            sx={{
              display: "grid",
              gap: 1.5,
              gridTemplateColumns: {
                xs: "1fr",
                sm: "repeat(2, 1fr)",
                lg: "repeat(3, 1fr)",
              },
            }}
          >
            {AREA_CARDS.map((card) => {
              const cardModules = modules.filter(card.predicate);
              if (card.id === "unknown" && cardModules.length === 0) {
                return null;
              }
              return (
                <AreaCard
                  key={card.id}
                  title={card.title}
                  modules={cardModules}
                  emptyHint={card.emptyHint}
                />
              );
            })}
          </Box>
        ) : (
          <Alert severity="info" variant="outlined">
            A study-plan dashboard will appear here once the backend extracts a plan from your chat.
          </Alert>
        )}

        {latestRuleCheck && <RuleCheckPanel result={latestRuleCheck} />}
      </Stack>

      <Snackbar
        open={Boolean(uploadError)}
        autoHideDuration={6000}
        onClose={() => setUploadError(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity="error" variant="filled" onClose={() => setUploadError(null)}>
          {uploadError}
        </Alert>
      </Snackbar>
    </Box>
  );
}
