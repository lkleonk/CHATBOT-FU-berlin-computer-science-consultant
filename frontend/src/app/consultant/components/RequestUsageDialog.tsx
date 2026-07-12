"use client";

import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import Button from "@mui/material/Button";
import LinearProgress from "@mui/material/LinearProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useEffect } from "react";

import { useUsage } from "@/context/UsageContext";
import type { UsageResponse } from "@/types/api";

type RequestUsageDialogProps = {
  open: boolean;
  onClose: () => void;
  usageOverride?: UsageResponse;
};

function formatResetTime(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function RequestUsageDialog({
  open,
  onClose,
  usageOverride,
}: RequestUsageDialogProps) {
  const { usage, isLoading, error, refreshUsage } = useUsage();

  useEffect(() => {
    if (open && !usageOverride) {
      void refreshUsage();
    }
  }, [open, refreshUsage, usageOverride]);

  const displayedUsage = usageOverride ?? usage;
  const displayedIsLoading = usageOverride ? false : isLoading;
  const displayedError = usageOverride ? null : error;
  const usedPercent = displayedUsage && displayedUsage.limit > 0
    ? (displayedUsage.used / displayedUsage.limit) * 100
    : 0;

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs" aria-labelledby="usage-title">
      <DialogTitle id="usage-title">Daily request allowance</DialogTitle>
      <DialogContent>
        <Stack spacing={1.5}>
          {displayedUsage ? (
            <>
              <Typography variant="h2">
                {displayedUsage.remaining} of {displayedUsage.limit} requests remaining
              </Typography>
              <LinearProgress variant="determinate" value={Math.min(100, usedPercent)} />
              <Typography variant="body2" sx={{ color: "text.secondary" }}>
                Each chat message or transcript upload uses one request. Your allowance resets at{" "}
                {formatResetTime(displayedUsage.reset_at)}.
              </Typography>
              <Typography variant="caption" sx={{ color: "text.secondary" }}>
                The allowance is currently associated with your client IP.
              </Typography>
            </>
          ) : (
            <Typography variant="body2" sx={{ color: displayedError ? "error.main" : "text.secondary" }}>
              {displayedError ?? (
                displayedIsLoading ? "Loading daily request allowance…" : "Daily request allowance unavailable."
              )}
            </Typography>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}
