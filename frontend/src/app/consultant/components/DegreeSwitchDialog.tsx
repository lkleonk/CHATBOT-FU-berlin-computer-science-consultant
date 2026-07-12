"use client";

import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import FactCheckOutlinedIcon from "@mui/icons-material/FactCheckOutlined";
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { DegreeInfo } from "@/types/api";

type DegreeSwitchDialogProps = {
  open: boolean;
  targetDegree: DegreeInfo | null;
  hasChatMessages: boolean;
  hasStudyPlan: boolean;
  onDownloadChat: () => void;
  onOpenStudyPlan: () => void;
  onCancel: () => void;
  onConfirm: () => void;
};

export function DegreeSwitchDialog({
  open,
  targetDegree,
  hasChatMessages,
  hasStudyPlan,
  onDownloadChat,
  onOpenStudyPlan,
  onCancel,
  onConfirm,
}: DegreeSwitchDialogProps) {
  return (
    <Dialog open={open} fullWidth maxWidth="sm" onClose={onCancel} aria-labelledby="degree-switch-title">
      <DialogTitle id="degree-switch-title">
        Switch to {targetDegree?.display_name ?? "another degree program"}?
      </DialogTitle>
      <DialogContent>
        <Alert severity="warning" sx={{ mb: 1.5 }}>
          Switching starts a fresh consultation for the new degree program. Your current chat,
          uploaded study plan, and validation results will be discarded.
        </Alert>
        <Typography variant="body2" sx={{ color: "text.secondary", mb: 1.5 }}>
          If you want to keep anything, save it before switching:
        </Typography>
        <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
          <Button
            size="small"
            variant="outlined"
            startIcon={<DownloadOutlinedIcon />}
            disabled={!hasChatMessages}
            onClick={onDownloadChat}
          >
            Download chat
          </Button>
          <Button
            size="small"
            variant="outlined"
            startIcon={<FactCheckOutlinedIcon />}
            disabled={!hasStudyPlan}
            onClick={onOpenStudyPlan}
          >
            Open Study Plan to print summary
          </Button>
        </Stack>
        <Typography variant="caption" sx={{ display: "block", color: "text.secondary", mt: 1 }}>
          Opening the Study Plan cancels the switch so you can print or save the module summary
          first; switch again afterwards.
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel}>Cancel</Button>
        <Button onClick={onConfirm} color="warning" variant="contained">
          Discard and switch
        </Button>
      </DialogActions>
    </Dialog>
  );
}
