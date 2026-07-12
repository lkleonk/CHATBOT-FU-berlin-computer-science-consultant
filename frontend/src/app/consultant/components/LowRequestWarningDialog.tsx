"use client";

import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";

type LowRequestWarningDialogProps = {
  open: boolean;
  remaining: number;
  onClose: () => void;
  onViewUsage: () => void;
};

export function LowRequestWarningDialog({
  open,
  remaining,
  onClose,
  onViewUsage,
}: LowRequestWarningDialogProps) {
  return (
    <Dialog open={open} onClose={onClose} aria-labelledby="low-requests-title">
      <DialogTitle id="low-requests-title">
        {remaining === 0 ? "No requests remaining today" : `Only ${remaining} requests remaining today`}
      </DialogTitle>
      <DialogContent>
        <DialogContentText>
          Each chat message or transcript upload uses one request.
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Continue</Button>
        <Button onClick={onViewUsage} variant="contained">
          View daily request allowance
        </Button>
      </DialogActions>
    </Dialog>
  );
}
