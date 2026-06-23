"use client";

import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import Typography from "@mui/material/Typography";

import { useUsage } from "@/context/UsageContext";

type WelcomeDialogProps = {
  open: boolean;
  onClose: () => void;
  onViewUsage: () => void;
};

export function WelcomeDialog({ open, onClose, onViewUsage }: WelcomeDialogProps) {
  const { usage } = useUsage();
  const retentionHours = usage ? Math.round(usage.session_inactivity_ttl_seconds / 3600) : null;

  return (
    <Dialog open={open} fullWidth maxWidth="sm" aria-labelledby="welcome-title">
      <DialogTitle id="welcome-title">Welcome to Modulio</DialogTitle>
      <DialogContent>
        <Alert severity="info" sx={{ mb: 1.5 }}>
          This is an unofficial service. Answers may be incomplete or incorrect and should be verified using official FU Berlin sources.
        </Alert>
        <List disablePadding>
          <ListItem disableGutters alignItems="flex-start">
            <ListItemIcon sx={{ minWidth: 36, mt: 0.5 }}>
              <InfoOutlinedIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText
              primary="Limited request allowance"
              secondary={
                usage
                  ? `${usage.remaining} of ${usage.limit} requests remain today. Messages and transcript uploads each use one request.`
                  : "Messages and transcript uploads are subject to a daily request allowance."
              }
            />
          </ListItem>
          <ListItem disableGutters alignItems="flex-start">
            <ListItemIcon sx={{ minWidth: 36, mt: 0.5 }}>
              <InfoOutlinedIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText
              primary="Temporary session data"
              secondary={
                retentionHours
                  ? `In-memory session data expires after ${retentionHours} hours of inactivity. Download your chat if you want to keep a copy.`
                  : "Session data is held temporarily. Download your chat if you want to keep a copy."
              }
            />
          </ListItem>
          <ListItem disableGutters alignItems="flex-start">
            <ListItemIcon sx={{ minWidth: 36, mt: 0.5 }}>
              <InfoOutlinedIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText
              primary="Transcript processing"
              secondary="Extracted transcript text is processed by the configured language model. Original PDF files are not included in chat exports."
            />
          </ListItem>
        </List>
        {usage?.diagnostic_tracing_enabled && (
          <Typography variant="caption" sx={{ display: "block", color: "warning.main", mt: 1 }}>
            Diagnostic tracing is enabled on this deployment and may retain unredacted prompts and transcript text separately from session state.
          </Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onViewUsage}>View request allowance</Button>
        <Button onClick={onClose} variant="contained" autoFocus>
          Start consultation
        </Button>
      </DialogActions>
    </Dialog>
  );
}
