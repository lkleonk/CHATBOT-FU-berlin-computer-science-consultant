"use client";

import UploadFileOutlinedIcon from "@mui/icons-material/UploadFileOutlined";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import IconButton from "@mui/material/IconButton";
import Tooltip from "@mui/material/Tooltip";
import { useCallback, useRef, useState, type ChangeEvent } from "react";

import { useSettings } from "@/context/SettingsContext";
import { useUsage } from "@/context/UsageContext";
import { ApiError, getApiErrorDetail, uploadTranscript } from "@/services/api";
import type { TranscriptUploadResponse } from "@/types/api";

import { UnreadablePdfDialog } from "./UnreadablePdfDialog";

type TranscriptUploadProps = {
  ensureSession: () => Promise<string>;
  onUploaded: (result: TranscriptUploadResponse) => void;
  onError?: (message: string) => void;
  disabled?: boolean;
  variant?: "icon" | "button";
};

function isPdf(file: File): boolean {
  return file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
}

export function TranscriptUpload({
  ensureSession,
  onUploaded,
  onError,
  disabled = false,
  variant = "icon",
}: TranscriptUploadProps) {
  const { updateQuota } = useUsage();
  const { tracingEnabled } = useSettings();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);

  const handleFileChange = useCallback(
    async (event: ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      // Reset so selecting the same file again still fires onChange.
      event.target.value = "";
      if (!file) {
        return;
      }
      if (!isPdf(file)) {
        onError?.("Only PDF files are supported.");
        return;
      }

      setIsUploading(true);
      try {
        const sessionId = await ensureSession();
        const response = await uploadTranscript(sessionId, file, tracingEnabled);
        updateQuota(response.usage);
        onUploaded(response.data);
      } catch (error) {
        if (error instanceof ApiError) {
          updateQuota(error.usage);
        }
        const detail = getApiErrorDetail(error);
        if (detail?.error_code === "pdf_unreadable") {
          setDialogOpen(true);
        } else {
          const message =
            error instanceof ApiError
              ? error.message
              : error instanceof Error
                ? error.message
                : "Failed to upload the PDF.";
          onError?.(message);
        }
      } finally {
        setIsUploading(false);
      }
    },
    [ensureSession, onError, onUploaded, tracingEnabled, updateQuota],
  );

  const triggerPicker = () => inputRef.current?.click();
  const isDisabled = disabled || isUploading;

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        hidden
        onChange={handleFileChange}
      />
      {variant === "icon" ? (
        <Tooltip title="Upload transcript PDF">
          <span>
            <IconButton
              onClick={triggerPicker}
              disabled={isDisabled}
              aria-label="Upload transcript PDF"
              sx={{ width: 48, height: 48 }}
            >
              {isUploading ? <CircularProgress size={20} /> : <UploadFileOutlinedIcon />}
            </IconButton>
          </span>
        </Tooltip>
      ) : (
        <Button
          onClick={triggerPicker}
          disabled={isDisabled}
          variant="outlined"
          startIcon={
            isUploading ? <CircularProgress size={16} /> : <UploadFileOutlinedIcon />
          }
        >
          {isUploading ? "Uploading…" : "Upload transcript PDF"}
        </Button>
      )}
      <UnreadablePdfDialog open={dialogOpen} onClose={() => setDialogOpen(false)} />
    </>
  );
}
