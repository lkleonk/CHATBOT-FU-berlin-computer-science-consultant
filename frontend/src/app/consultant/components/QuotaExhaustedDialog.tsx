"use client";

import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";

function formatResetTime(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

type QuotaExhaustedDialogProps = {
  open: boolean;
  resetAt: string | null;
  onClose: () => void;
  onBrowseRegistry: () => void;
};

export function QuotaExhaustedDialog({
  open,
  resetAt,
  onClose,
  onBrowseRegistry,
}: QuotaExhaustedDialogProps) {
  return (
    <Dialog open={open} onClose={onClose} aria-labelledby="quota-exhausted-title">
      <DialogTitle id="quota-exhausted-title">Daily request limit reached</DialogTitle>
      <DialogContent>
        <DialogContentText>
          You have used all of your requests for today, so chat and transcript checks are
          paused{resetAt ? ` until ${formatResetTime(resetAt)}` : " until the daily allowance resets"}.
          In the meantime you can still browse the Course Registry and Degree Rules.
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Stay in chat</Button>
        <Button onClick={onBrowseRegistry} variant="contained">
          Browse Course Registry
        </Button>
      </DialogActions>
    </Dialog>
  );
}
