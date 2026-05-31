"use client";

import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";

type UnreadablePdfDialogProps = {
  open: boolean;
  onClose: () => void;
};

export function UnreadablePdfDialog({ open, onClose }: UnreadablePdfDialogProps) {
  return (
    <Dialog open={open} onClose={onClose} aria-labelledby="unreadable-pdf-title">
      <DialogTitle id="unreadable-pdf-title">Unreadable PDF</DialogTitle>
      <DialogContent>
        <DialogContentText>
          This PDF appears to be unreadable. Please upload a text-based PDF.
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} autoFocus>
          OK
        </Button>
      </DialogActions>
    </Dialog>
  );
}
