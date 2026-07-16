"use client";

import Alert from "@mui/material/Alert";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import Button from "@mui/material/Button";
import Divider from "@mui/material/Divider";
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
  const service = displayedUsage?.service;
  const serviceUsedPercent = service && service.limit > 0
    ? (service.used / service.limit) * 100
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

              {service && (
                <>
                  <Divider sx={{ mt: 0.5 }} />
                  <Typography variant="overline" sx={{ color: "text.secondary" }}>
                    Service-wide
                  </Typography>
                  {service.remaining > 0 ? (
                    <>
                      <Typography variant="body1" sx={{ fontWeight: 700 }}>
                        {service.remaining} of {service.limit} requests remaining
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={Math.min(100, serviceUsedPercent)}
                        color={serviceUsedPercent >= 80 ? "warning" : "primary"}
                      />
                      <Typography variant="body2" sx={{ color: "text.secondary" }}>
                        All users share this daily budget, counted in the same requests as your own
                        allowance. When it runs out, requests stop for everyone until it resets —
                        even if you have some of your own left.
                      </Typography>
                    </>
                  ) : (
                    <Alert severity="warning">
                      The service-wide daily limit is used up, so requests will fail until it resets
                      — even though you have {displayedUsage.remaining} of your own left.
                    </Alert>
                  )}
                </>
              )}
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
