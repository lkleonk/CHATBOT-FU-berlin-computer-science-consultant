"use client";

import AutoAwesomeOutlinedIcon from "@mui/icons-material/AutoAwesomeOutlined";
import CheckOutlinedIcon from "@mui/icons-material/CheckOutlined";
import CloseOutlinedIcon from "@mui/icons-material/CloseOutlined";
import ContentCopyOutlinedIcon from "@mui/icons-material/ContentCopyOutlined";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import IconButton from "@mui/material/IconButton";
import Snackbar from "@mui/material/Snackbar";
import Tooltip from "@mui/material/Tooltip";
import { alpha } from "@mui/material/styles";
import Typography from "@mui/material/Typography";
import { useState } from "react";

const WIZARDFLOW_URL = "https://getwizardflow.com";
const INSTALL_COMMAND = "pip install wizardflow";

type WizardFlowPromoProps = {
  open: boolean;
  onClose: () => void;
};

export function WizardFlowPromo({ open, onClose }: WizardFlowPromoProps) {
  const [copied, setCopied] = useState(false);

  const copyInstall = async () => {
    try {
      await navigator.clipboard.writeText(INSTALL_COMMAND);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard unavailable (e.g. insecure context); leave the command visible to copy manually.
    }
  };

  return (
    <Snackbar open={open} anchorOrigin={{ vertical: "bottom", horizontal: "right" }}>
      <Alert
        icon={<AutoAwesomeOutlinedIcon fontSize="inherit" />}
        severity="info"
        variant="filled"
        sx={{ maxWidth: 360, alignItems: "flex-start", boxShadow: 6 }}
        action={
          <IconButton
            size="small"
            color="inherit"
            aria-label="Dismiss"
            onClick={onClose}
            sx={{ mt: -0.5 }}
          >
            <CloseOutlinedIcon fontSize="small" />
          </IconButton>
        }
      >
        <Typography variant="subtitle2" sx={{ fontWeight: 700, lineHeight: 1.35, mb: 0.75 }}>
          Tired of reading agent logs line by line?
        </Typography>
        <Typography variant="body2" sx={{ mb: 1.5 }}>
          WizardFlow is a new open-source Python SDK that records your agent runs and
          replays them as an interactive graph — the same one powering this chatbot
          under the hood.
        </Typography>
        <Tooltip title={copied ? "Copied!" : "Click to copy"} placement="top">
          <Box
            component="button"
            type="button"
            onClick={copyInstall}
            aria-label={`Copy install command: ${INSTALL_COMMAND}`}
            sx={{
              display: "flex",
              width: "100%",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 1,
              mb: 1.5,
              px: 1.25,
              py: 0.75,
              border: 0,
              borderRadius: 1,
              cursor: "pointer",
              color: "common.white",
              bgcolor: (theme) => alpha(theme.palette.common.black, 0.5),
              transition: (theme) => theme.transitions.create("background-color"),
              "&:hover": { bgcolor: (theme) => alpha(theme.palette.common.black, 0.62) },
            }}
          >
            <Box component="code" sx={{ fontFamily: "monospace", fontSize: "0.8125rem" }}>
              {INSTALL_COMMAND}
            </Box>
            {copied ? (
              <CheckOutlinedIcon sx={{ fontSize: 16, flexShrink: 0 }} />
            ) : (
              <ContentCopyOutlinedIcon sx={{ fontSize: 16, flexShrink: 0, opacity: 0.85 }} />
            )}
          </Box>
        </Tooltip>
        <Button
          fullWidth
          size="small"
          variant="contained"
          href={WIZARDFLOW_URL}
          target="_blank"
          rel="noopener noreferrer"
          onClick={onClose}
          sx={{
            bgcolor: "common.white",
            color: (theme) => theme.palette.info.dark,
            fontWeight: 600,
            "&:hover": { bgcolor: "grey.200" },
          }}
        >
          Visit getwizardflow.com
        </Button>
      </Alert>
    </Snackbar>
  );
}
