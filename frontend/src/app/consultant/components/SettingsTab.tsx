"use client";

import AddCircleOutlineOutlinedIcon from "@mui/icons-material/AddCircleOutlineOutlined";
import DataUsageOutlinedIcon from "@mui/icons-material/DataUsageOutlined";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutlined";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import RefreshOutlinedIcon from "@mui/icons-material/RefreshOutlined";
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
import Stack from "@mui/material/Stack";
import Switch from "@mui/material/Switch";
import Typography from "@mui/material/Typography";
import { useCallback, useEffect, useState } from "react";

import { DEV_TOOLS_ENABLED } from "@/config/publicConfig";
import { useSettings } from "@/context/SettingsContext";
import { useUsage } from "@/context/UsageContext";
import { API_BASE_URL, getHealth } from "@/services/api";
import type { HealthResponse } from "@/types/api";

import { downloadStoredChat } from "./chatExport";
import { loadStoredChatMessages } from "./chatMessages";

type SettingsTabProps = {
  sessionId: string | null;
  onClearLocalState: () => Promise<void>;
  onLoadDummyData: () => void;
  onOpenUsage: () => void;
};

export function SettingsTab({
  sessionId,
  onClearLocalState,
  onLoadDummyData,
  onOpenUsage,
}: SettingsTabProps) {
  const { darkMode, toggleDarkMode } = useSettings();
  const { usage } = useUsage();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [resetError, setResetError] = useState<string | null>(null);
  const [isResetting, setIsResetting] = useState(false);
  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const [hasDownloadableChat, setHasDownloadableChat] = useState(false);

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
              Appearance, request allowance, and conversation data.
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
              Request allowance
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
                <Typography variant="h3" sx={{ mb: 1 }}>
                  Developer
                </Typography>
                <Stack spacing={1.25}>
                  <Stack direction="row" spacing={0.75} sx={{ flexWrap: "wrap" }}>
                    <Chip label={`API: ${API_BASE_URL}`} variant="outlined" />
                    <Chip label={`Session: ${sessionId ?? "none"}`} variant="outlined" />
                    {health && (
                      <Chip
                        label={`Health: ${health.status}`}
                        color={health.status === "healthy" ? "success" : "warning"}
                      />
                    )}
                  </Stack>

                  {healthError && <Alert severity="error">{healthError}</Alert>}

                  {health && (
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
                  )}

                  <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
                    <Button
                      startIcon={<AddCircleOutlineOutlinedIcon />}
                      onClick={onLoadDummyData}
                      variant="contained"
                    >
                      Set Dummy Data
                    </Button>
                    <Button
                      startIcon={<RefreshOutlinedIcon />}
                      onClick={() => void refreshHealth()}
                      disabled={isRefreshing}
                      variant="outlined"
                    >
                      Refresh Health
                    </Button>
                  </Stack>
                </Stack>
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
            <Button startIcon={<DownloadOutlinedIcon />} onClick={() => downloadStoredChat()}>
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
