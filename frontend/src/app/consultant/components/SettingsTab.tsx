"use client";

import DataUsageOutlinedIcon from "@mui/icons-material/DataUsageOutlined";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutlined";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import ErrorOutlineOutlinedIcon from "@mui/icons-material/ErrorOutlineOutlined";
import NoteAddOutlinedIcon from "@mui/icons-material/NoteAddOutlined";
import RefreshOutlinedIcon from "@mui/icons-material/RefreshOutlined";
import SchoolOutlinedIcon from "@mui/icons-material/SchoolOutlined";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import Divider from "@mui/material/Divider";
import FormControlLabel from "@mui/material/FormControlLabel";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Switch from "@mui/material/Switch";
import Typography from "@mui/material/Typography";
import { useCallback, useEffect, useState } from "react";

import { DEV_TOOLS_ENABLED } from "@/config/publicConfig";
import { useSettings } from "@/context/SettingsContext";
import { useUsage } from "@/context/UsageContext";
import { API_BASE_URL, getHealth, reinitTracing } from "@/services/api";
import type { HealthResponse } from "@/types/api";

import { loadStoredChatMessages } from "./chatMessages";

const dialogPreviewButtonSx = {
  minHeight: 44,
  px: 2,
  justifyContent: "flex-start",
  flex: { xs: "1 1 100%", sm: "1 1 260px" },
  color: "text.primary",
  borderColor: "divider",
  bgcolor: "background.paper",
  "&:hover": {
    borderColor: "text.secondary",
    bgcolor: "action.hover",
  },
};

const developerActionButtonSx = {
  minHeight: 44,
  px: 2,
  flex: { xs: "1 1 100%", sm: "0 1 auto" },
};

type SettingsTabProps = {
  sessionId: string | null;
  onClearLocalState: () => Promise<void>;
  onShowFailedChatRequest: () => void;
  onShowUsagePreview: () => void;
  onOpenUsage: () => void;
  onShowWelcome: () => void;
  onOpenChatExport: () => void;
};

export function SettingsTab({
  sessionId,
  onClearLocalState,
  onShowFailedChatRequest,
  onShowUsagePreview,
  onOpenUsage,
  onShowWelcome,
  onOpenChatExport,
}: SettingsTabProps) {
  const {
    darkMode,
    toggleDarkMode,
    courseRegistryPreviewEnabled,
    setCourseRegistryPreviewEnabled,
    studyPlanPreviewEnabled,
    setStudyPlanPreviewEnabled,
  } = useSettings();
  const { usage } = useUsage();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [resetError, setResetError] = useState<string | null>(null);
  const [isResetting, setIsResetting] = useState(false);
  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const [hasDownloadableChat, setHasDownloadableChat] = useState(false);
  const [isRotatingTrace, setIsRotatingTrace] = useState(false);
  const [tracePath, setTracePath] = useState<string | null>(null);
  const [traceError, setTraceError] = useState<string | null>(null);

  const refreshHealth = useCallback(async () => {
    if (!DEV_TOOLS_ENABLED) {
      return;
    }
    setIsRefreshing(true);
    setHealthError(null);
    try {
      setHealth(await getHealth());
    } catch (error) {
      setHealth(null);
      setHealthError(error instanceof Error ? error.message : "Backend health check failed.");
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    if (!DEV_TOOLS_ENABLED) {
      return;
    }
    const timer = window.setTimeout(() => {
      void refreshHealth();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [refreshHealth]);

  const startNewTraceFile = async () => {
    setIsRotatingTrace(true);
    setTracePath(null);
    setTraceError(null);
    try {
      const result = await reinitTracing();
      setTracePath(result.trace_path);
    } catch (error) {
      setTraceError(error instanceof Error ? error.message : "Starting a new trace file failed.");
    } finally {
      setIsRotatingTrace(false);
    }
  };

  const openResetDialog = () => {
    setResetError(null);
    setHasDownloadableChat(loadStoredChatMessages().length > 0);
    setResetDialogOpen(true);
  };

  const resetConversation = async () => {
    setIsResetting(true);
    setResetError(null);
    try {
      await onClearLocalState();
      setResetDialogOpen(false);
    } catch (error) {
      setResetError(error instanceof Error ? error.message : "Conversation reset failed.");
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <>
      <Box sx={{ height: "100%", overflowY: "auto", px: { xs: 1.5, md: 3 }, py: 2 }}>
        <Stack spacing={2.5} sx={{ maxWidth: 860, mx: "auto" }}>
          <Box>
            <Typography variant="h2" sx={{ mb: 0.5 }}>
              Settings
            </Typography>
            <Typography variant="body2" sx={{ color: "text.secondary" }}>
              Appearance, daily request allowance, and conversation data.
            </Typography>
          </Box>

          <Box>
            <Typography variant="h3" sx={{ mb: 1 }}>
              Appearance
            </Typography>
            <FormControlLabel
              control={<Switch checked={darkMode} onChange={toggleDarkMode} />}
              label="Dark mode"
            />
          </Box>

          <Divider />

          <Box>
            <Typography variant="h3" sx={{ mb: 1 }}>
              Daily request allowance
            </Typography>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ alignItems: { sm: "center" } }}>
              <Chip
                icon={<DataUsageOutlinedIcon />}
                label={usage ? `${usage.remaining} of ${usage.limit} remaining` : "Usage unavailable"}
                color={usage && usage.remaining <= 10 ? "warning" : "default"}
                variant="outlined"
              />
              <Button onClick={onOpenUsage} variant="outlined">
                View details
              </Button>
            </Stack>
          </Box>

          <Divider />

          <Box>
            <Typography variant="h3" sx={{ mb: 1 }}>
              Data and conversation
            </Typography>
            <Typography variant="body2" sx={{ color: "text.secondary", mb: 1.25 }}>
              Resetting deletes the current backend session and clears locally stored chat and study-plan data.
            </Typography>
            {resetError && <Alert severity="error" sx={{ mb: 1.25 }}>{resetError}</Alert>}
            <Button
              startIcon={<DeleteOutlineIcon />}
              onClick={openResetDialog}
              disabled={isResetting}
              color="error"
              variant="outlined"
            >
              Reset conversation
            </Button>
          </Box>

          {DEV_TOOLS_ENABLED && (
            <>
              <Divider />
              <Box>
                <Typography variant="h3" sx={{ mb: 1.25 }}>
                  Developer
                </Typography>
                <Paper variant="outlined" sx={{ p: { xs: 1.5, sm: 2 }, bgcolor: "background.paper" }}>
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="overline" sx={{ color: "text.secondary" }}>
                      Backend connection
                    </Typography>
                    <Stack direction="row" spacing={0.75} sx={{ flexWrap: "wrap", mt: 0.5 }}>
                    <Chip label={`API: ${API_BASE_URL}`} variant="outlined" />
                    <Chip label={`Session: ${sessionId ?? "none"}`} variant="outlined" />
                    {health && (
                      <Chip
                        label={`Health: ${health.status}`}
                        color={health.status === "healthy" ? "success" : "warning"}
                      />
                    )}
                  </Stack>
                  </Box>

                  {healthError && <Alert severity="error">{healthError}</Alert>}

                  {health && (
                    <Box sx={{ px: 1.5, border: 1, borderColor: "divider", borderRadius: 1.5 }}>
                    <List dense disablePadding>
                      {Object.entries(health.services).map(([service, status]) => (
                        <ListItem key={service} disableGutters>
                          <ListItemText
                            primary={
                              <Typography variant="body2" sx={{ fontWeight: 700 }}>
                                {service}
                              </Typography>
                            }
                            secondary={status}
                          />
                        </ListItem>
                      ))}
                    </List>
                    </Box>
                  )}

                  <Stack
                    direction={{ xs: "column", sm: "row" }}
                    useFlexGap
                    sx={{ flexWrap: "wrap", gap: 1.25 }}
                  >
                    <Button
                      startIcon={<RefreshOutlinedIcon />}
                      onClick={() => void refreshHealth()}
                      disabled={isRefreshing}
                      variant="outlined"
                      sx={developerActionButtonSx}
                    >
                      Refresh Health
                    </Button>
                    {usage?.diagnostic_tracing_enabled && (
                      <Button
                        startIcon={<NoteAddOutlinedIcon />}
                        onClick={() => void startNewTraceFile()}
                        disabled={isRotatingTrace}
                        variant="outlined"
                        sx={developerActionButtonSx}
                      >
                        {isRotatingTrace ? "Starting…" : "New Trace File"}
                      </Button>
                    )}
                  </Stack>

                  {traceError && <Alert severity="error">{traceError}</Alert>}
                  {tracePath && (
                    <Alert severity="success">
                      New trace file started: <code>{tracePath}</code>
                    </Alert>
                  )}

                  <Box>
                    <Typography variant="overline" sx={{ color: "text.secondary" }}>
                      Local previews
                    </Typography>
                    <Stack spacing={1.25} sx={{ mt: 0.5 }}>
                    <Box sx={{ p: 1.5, border: 1, borderColor: "divider", borderRadius: 1.5 }}>
                    <Typography variant="body1" sx={{ mb: 0.25, fontWeight: 700 }}>
                      Course Registry preview
                    </Typography>
                    <FormControlLabel
                      sx={{ m: 0, mt: 0.25 }}
                      control={
                        <Switch
                          checked={courseRegistryPreviewEnabled}
                          onChange={(_, checked) => setCourseRegistryPreviewEnabled(checked)}
                        />
                      }
                      label="Use bundled dummy data"
                    />
                    <Typography variant="body2" sx={{ color: "text.secondary" }}>
                      Lets the Course Registry run without a backend. The bundled example offerings are clearly marked as dummy data.
                    </Typography>
                    </Box>

                    <Box sx={{ p: 1.5, border: 1, borderColor: "divider", borderRadius: 1.5 }}>
                    <Typography variant="body1" sx={{ mb: 0.25, fontWeight: 700 }}>
                      Study Plan preview
                    </Typography>
                    <FormControlLabel
                      sx={{ m: 0, mt: 0.25 }}
                      control={
                        <Switch
                          checked={studyPlanPreviewEnabled}
                          onChange={(_, checked) => setStudyPlanPreviewEnabled(checked)}
                        />
                      }
                      label="Use partial transcript demo data"
                    />
                    <Typography variant="body2" sx={{ color: "text.secondary" }}>
                      Loads a small M.Sc. Informatik subset from the local Max Mustermann demo transcript. It is not a complete transcript or a rule-check result.
                    </Typography>
                    </Box>
                    </Stack>
                  </Box>

                  <Box>
                    <Typography variant="overline" sx={{ color: "text.secondary" }}>
                      Dialog previews
                    </Typography>
                    <Stack
                      direction={{ xs: "column", sm: "row" }}
                      useFlexGap
                      sx={{ flexWrap: "wrap", gap: 1.25, mt: 0.5 }}
                    >
                      <Button
                        startIcon={<DataUsageOutlinedIcon />}
                        onClick={onShowUsagePreview}
                        variant="outlined"
                        sx={dialogPreviewButtonSx}
                      >
                        Show daily request allowance dialog
                      </Button>
                      <Button
                        startIcon={<ErrorOutlineOutlinedIcon />}
                        onClick={onShowFailedChatRequest}
                        variant="outlined"
                        sx={dialogPreviewButtonSx}
                      >
                        Show failed chat request dialog
                      </Button>
                      <Button
                        startIcon={<SchoolOutlinedIcon />}
                        onClick={onShowWelcome}
                        variant="outlined"
                        sx={dialogPreviewButtonSx}
                      >
                        Show welcome dialog
                      </Button>
                    </Stack>
                  </Box>
                </Stack>
                </Paper>
              </Box>
            </>
          )}
        </Stack>
      </Box>

      <Dialog open={resetDialogOpen} onClose={() => setResetDialogOpen(false)} aria-labelledby="reset-conversation-title">
        <DialogTitle id="reset-conversation-title">Reset conversation?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            This permanently clears the current conversation and study-plan state. Download the chat first if you want to keep a copy.
          </DialogContentText>
          {resetError && <Alert severity="error" sx={{ mt: 1.5 }}>{resetError}</Alert>}
        </DialogContent>
        <DialogActions>
          {hasDownloadableChat && (
            <Button startIcon={<DownloadOutlinedIcon />} onClick={onOpenChatExport}>
              Download chat
            </Button>
          )}
          <Button onClick={() => setResetDialogOpen(false)} disabled={isResetting}>
            Cancel
          </Button>
          <Button
            onClick={() => void resetConversation()}
            disabled={isResetting}
            color="error"
            variant="contained"
          >
            {isResetting ? "Resetting…" : "Reset conversation"}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
