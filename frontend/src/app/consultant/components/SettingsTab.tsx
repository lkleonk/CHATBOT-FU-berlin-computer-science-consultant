"use client";

import AddCircleOutlineOutlinedIcon from "@mui/icons-material/AddCircleOutlineOutlined";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutlined";
import RefreshOutlinedIcon from "@mui/icons-material/RefreshOutlined";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import FormControlLabel from "@mui/material/FormControlLabel";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Stack from "@mui/material/Stack";
import Switch from "@mui/material/Switch";
import Typography from "@mui/material/Typography";
import { useCallback, useEffect, useState } from "react";

import { API_BASE_URL, getHealth } from "@/services/api";
import type { HealthResponse } from "@/types/api";
import { useSettings } from "@/context/SettingsContext";

type SettingsTabProps = {
  sessionId: string | null;
  onClearLocalState: () => void;
  onLoadDummyData: () => void;
};

export function SettingsTab({ sessionId, onClearLocalState, onLoadDummyData }: SettingsTabProps) {
  const { darkMode, toggleDarkMode } = useSettings();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const refreshHealth = useCallback(async () => {
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
    const timer = window.setTimeout(() => {
      void refreshHealth();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [refreshHealth]);

  return (
    <Box sx={{ height: "100%", overflowY: "auto", px: { xs: 1.5, md: 3 }, py: 2 }}>
      <Stack spacing={2.5} sx={{ maxWidth: 860, mx: "auto" }}>
        <Box>
          <Typography variant="h2" sx={{ mb: 0.5 }}>
            Settings
          </Typography>
          <Typography variant="body2" sx={{ color: "text.secondary" }}>
            Local browser settings and backend diagnostics.
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
              <Button
                startIcon={<DeleteOutlineIcon />}
                onClick={onClearLocalState}
                color="error"
                variant="outlined"
              >
                Reset Session
              </Button>
            </Stack>
          </Stack>
        </Box>
      </Stack>
    </Box>
  );
}
