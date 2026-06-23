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

type RequestUsageDialogProps = {
  open: boolean;
  onClose: () => void;
};

function formatResetTime(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function RequestUsageDialog({ open, onClose }: RequestUsageDialogProps) {
  const { usage, isLoading, error, refreshUsage } = useUsage();

  useEffect(() => {
    if (open) {
      void refreshUsage();
    }
  }, [open, refreshUsage]);

  const usedPercent = usage && usage.limit > 0 ? (usage.used / usage.limit) * 100 : 0;

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs" aria-labelledby="usage-title">
      <DialogTitle id="usage-title">Request allowance</DialogTitle>
      <DialogContent>
        <Stack spacing={1.5}>
          {usage ? (
            <>
              <Typography variant="h2">
                {usage.remaining} of {usage.limit} requests remaining
              </Typography>
              <LinearProgress variant="determinate" value={Math.min(100, usedPercent)} />
              <Typography variant="body2" sx={{ color: "text.secondary" }}>
                Each chat message or transcript upload uses one request. Your allowance resets at{" "}
                {formatResetTime(usage.reset_at)}.
              </Typography>
              <Typography variant="caption" sx={{ color: "text.secondary" }}>
                The allowance is currently associated with your client IP.
              </Typography>
            </>
          ) : (
            <Typography variant="body2" sx={{ color: error ? "error.main" : "text.secondary" }}>
              {error ?? (isLoading ? "Loading request allowance…" : "Request allowance unavailable.")}
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
