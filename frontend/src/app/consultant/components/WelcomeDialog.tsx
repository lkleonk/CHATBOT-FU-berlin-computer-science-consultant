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
import Stack from "@mui/material/Stack";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import Typography from "@mui/material/Typography";
import { useState } from "react";

import { useDegree } from "@/context/DegreeContext";
import { useUsage } from "@/context/UsageContext";

type WelcomeDialogProps = {
  open: boolean;
  onClose: (degreeId: string) => void;
  onViewUsage: (degreeId: string) => void;
};

export function WelcomeDialog({ open, onClose, onViewUsage }: WelcomeDialogProps) {
  const { usage } = useUsage();
  const { degreeId, degrees } = useDegree();
  const [pickedDegree, setPickedDegree] = useState<string | null>(null);
  // An explicit pick wins; otherwise preselect the previously stored choice.
  const selectedDegree = pickedDegree ?? degreeId;
  const retentionHours = usage ? Math.round(usage.session_inactivity_ttl_seconds / 3600) : null;

  return (
    <Dialog open={open} fullWidth maxWidth="sm" aria-labelledby="welcome-title">
      <DialogTitle id="welcome-title">Welcome to Modulio</DialogTitle>
      <DialogContent>
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          Choose your degree program
        </Typography>
        <ToggleButtonGroup
          exclusive
          fullWidth
          value={selectedDegree}
          onChange={(_, nextDegree: string | null) => {
            if (nextDegree) {
              setPickedDegree(nextDegree);
            }
          }}
          aria-label="Degree program"
          orientation="vertical"
          sx={{ mb: 2 }}
        >
          {degrees.map((degree) => (
            <ToggleButton
              key={degree.id}
              value={degree.id}
              sx={{
                justifyContent: "flex-start",
                textAlign: "left",
                textTransform: "none",
                py: 1.25,
              }}
            >
              <Stack spacing={0.25}>
                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  {degree.display_name}
                </Typography>
                <Typography variant="caption" sx={{ color: "text.secondary" }}>
                  {degree.regulation}
                </Typography>
              </Stack>
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
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
        <Button disabled={!selectedDegree} onClick={() => selectedDegree && onViewUsage(selectedDegree)}>
          View request allowance
        </Button>
        <Button
          onClick={() => selectedDegree && onClose(selectedDegree)}
          variant="contained"
          autoFocus
          disabled={!selectedDegree}
        >
          Start consultation
        </Button>
      </DialogActions>
    </Dialog>
  );
}
