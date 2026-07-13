"use client";

import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import SendOutlinedIcon from "@mui/icons-material/SendOutlined";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Collapse from "@mui/material/Collapse";
import IconButton from "@mui/material/IconButton";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useDegree } from "@/context/DegreeContext";
import { useUsage } from "@/context/UsageContext";
import { ApiError, createSession, sendMessage } from "@/services/api";
import type { RuleCheckResult, StudyPlan, TranscriptUploadResponse } from "@/types/api";

import {
  buildTranscriptChatMessages,
  createMessageId,
  loadStoredChatMessages,
  type ChatMessage,
} from "./chatMessages";
import { CitationList } from "./CitationList";
import { ChatErrorDialog, DEFAULT_CHAT_ERROR_MESSAGE } from "./ChatErrorDialog";
import { RuleCheckPanel } from "./RuleCheckPanel";
import { TranscriptUpload } from "./TranscriptUpload";
import { CHAT_MESSAGES_STORAGE_KEY, SESSION_ID_STORAGE_KEY } from "./storage";

type ChatTabProps = {
  sessionId: string | null;
  onSessionIdChange: (sessionId: string | null) => void;
  onRuleCheckResult: (result: RuleCheckResult | null) => void;
  onStudyPlan: (plan: StudyPlan | null) => void;
  onMessagesChange: (messages: ChatMessage[]) => void;
};

function countRuleIssues(result: RuleCheckResult) {
  return {
    errors: result.issues.filter((issue) => issue.severity === "error").length,
    warnings: result.issues.filter((issue) => issue.severity === "warning").length,
  };
}

export function ChatTab({
  sessionId,
  onSessionIdChange,
  onRuleCheckResult,
  onStudyPlan,
  onMessagesChange,
}: ChatTabProps) {
  const { updateQuota } = useUsage();
  const { effectiveDegreeId } = useDegree();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorDialogOpen, setErrorDialogOpen] = useState(false);
  const [expandedRuleMessageId, setExpandedRuleMessageId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const hasLoadedStoredMessages = useRef(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const storedMessages = loadStoredChatMessages();
      setMessages(storedMessages);
      const reversed = [...storedMessages].reverse();
      const latestRuleCheck = reversed.find((message) => message.ruleCheckResult)?.ruleCheckResult;
      const latestStudyPlan = reversed.find((message) => message.parsedStudyPlan)?.parsedStudyPlan;
      onRuleCheckResult(latestRuleCheck ?? null);
      onStudyPlan(latestStudyPlan ?? null);
      hasLoadedStoredMessages.current = true;
    }, 0);

    return () => window.clearTimeout(timer);
  }, [onRuleCheckResult, onStudyPlan]);

  useEffect(() => {
    if (!hasLoadedStoredMessages.current) {
      return;
    }
    window.sessionStorage.setItem(CHAT_MESSAGES_STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    onMessagesChange(messages);
  }, [messages, onMessagesChange]);

  useEffect(() => {
    if (sessionId) {
      window.sessionStorage.setItem(SESSION_ID_STORAGE_KEY, sessionId);
    }
  }, [sessionId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, isLoading]);

  const canSend = useMemo(() => input.trim().length > 0 && !isLoading, [input, isLoading]);

  const showError = useCallback((message: string) => {
    setError(message);
    setErrorDialogOpen(true);
  }, []);

  const ensureSession = useCallback(async () => {
    if (sessionId) {
      return sessionId;
    }

    const created = await createSession(effectiveDegreeId);
    onSessionIdChange(created.session_id);
    window.sessionStorage.setItem(SESSION_ID_STORAGE_KEY, created.session_id);
    return created.session_id;
  }, [effectiveDegreeId, onSessionIdChange, sessionId]);

  const handleSubmit = useCallback(async () => {
    const content = input.trim();
    if (!content || isLoading) {
      return;
    }

    setError(null);
    setErrorDialogOpen(false);
    setInput("");
    setIsLoading(true);

    const userMessage: ChatMessage = {
      id: createMessageId(),
      role: "user",
      content,
    };
    setMessages((current) => [...current, userMessage]);

    try {
      const activeSessionId = await ensureSession();
      const response = await sendMessage(activeSessionId, content);
      updateQuota(response.usage);
      const reply = response.data;
      const assistantMessage: ChatMessage = {
        id: createMessageId(),
        role: "assistant",
        content: reply.reply,
        messageType: reply.message_type,
        citations: reply.citations,
        ruleCheckResult: reply.rule_check_result,
        parsedStudyPlan: reply.parsed_study_plan,
      };

      setMessages((current) => [...current, assistantMessage]);
      onRuleCheckResult(reply.rule_check_result);
      if (reply.parsed_study_plan) {
        onStudyPlan(reply.parsed_study_plan);
      }
    } catch (sendError) {
      if (sendError instanceof ApiError) {
        updateQuota(sendError.usage);
      }
      showError(sendError instanceof Error ? sendError.message : "The message could not be sent.");
    } finally {
      setIsLoading(false);
    }
  }, [
    ensureSession,
    input,
    isLoading,
    onRuleCheckResult,
    onStudyPlan,
    showError,
    updateQuota,
  ]);

  const handleTranscriptUploaded = useCallback(
    (result: TranscriptUploadResponse) => {
      setError(null);
      setMessages((current) => [...current, ...buildTranscriptChatMessages(result)]);
      onRuleCheckResult(result.rule_check_result);
      if (result.parsed_study_plan) {
        onStudyPlan(result.parsed_study_plan);
      }
    },
    [onRuleCheckResult, onStudyPlan],
  );

  return (
    <Box sx={{ height: "100%", minHeight: 0, display: "flex", flexDirection: "column" }}>
      <Box
        ref={scrollRef}
        sx={{
          flex: 1,
          minHeight: 0,
          overflowY: "auto",
          px: { xs: 1.5, md: 3 },
          py: 2,
        }}
      >
        <Stack spacing={1.5} sx={{ maxWidth: 980, mx: "auto" }}>
          {messages.length === 0 && (
            <Paper variant="outlined" sx={{ p: 2, bgcolor: "background.paper" }}>
              <Typography variant="h2" sx={{ mb: 0.75 }}>
                FU Berlin Master Informatik
              </Typography>
              <Typography variant="body2" sx={{ color: "text.secondary" }}>
                Ask a study-rule question or paste a draft study plan.
              </Typography>
            </Paper>
          )}

          {messages.map((message) => {
            const isUser = message.role === "user";
            const ruleCheckResult =
              !isUser && message.messageType === "plan_check" ? message.ruleCheckResult : null;
            const isRuleExpanded = expandedRuleMessageId === message.id;
            const ruleIssueCounts = ruleCheckResult ? countRuleIssues(ruleCheckResult) : null;

            return (
              <Box
                key={message.id}
                sx={{
                  display: "flex",
                  justifyContent: isUser ? "flex-end" : "flex-start",
                }}
              >
                <Paper
                  variant="outlined"
                  sx={{
                    p: 1.5,
                    maxWidth: "min(780px, 100%)",
                    bgcolor: (theme) =>
                      isUser
                        ? theme.palette.mode === "dark"
                          ? theme.palette.primary.dark
                          : theme.palette.primary.main
                        : theme.palette.background.paper,
                    color: (theme) =>
                      isUser
                        ? theme.palette.mode === "dark"
                          ? theme.palette.common.white
                          : theme.palette.primary.contrastText
                        : theme.palette.text.primary,
                    borderColor: isUser ? "primary.dark" : "divider",
                  }}
                >
                  <Typography
                    variant="caption"
                    sx={{
                      display: "block",
                      mb: 0.5,
                      fontWeight: 700,
                      color: isUser ? "inherit" : "text.secondary",
                    }}
                  >
                    {isUser ? "You" : "Assistant"}
                  </Typography>
                  <Typography variant="body1" sx={{ whiteSpace: "pre-wrap" }}>
                    {message.content}
                  </Typography>
                  {!isUser && <CitationList citations={message.citations ?? []} />}
                  {ruleCheckResult && ruleIssueCounts && (
                    <Box
                      sx={{
                        mt: 1.5,
                        p: 1,
                        border: 1,
                        borderColor: "divider",
                        borderRadius: 1,
                        bgcolor: "action.hover",
                      }}
                    >
                      <Stack
                        direction={{ xs: "column", sm: "row" }}
                        spacing={1}
                        sx={{
                          alignItems: { xs: "flex-start", sm: "center" },
                          justifyContent: "space-between",
                        }}
                      >
                        <Stack direction="row" spacing={0.75} sx={{ alignItems: "center", flexWrap: "wrap" }}>
                          <Typography variant="caption" sx={{ fontWeight: 700 }}>
                            Rule Check
                          </Typography>
                          <Chip
                            label={ruleCheckResult.is_valid ? "Valid" : "Needs changes"}
                            color={ruleCheckResult.is_valid ? "success" : "error"}
                            size="small"
                          />
                          <Chip
                            label={`${ruleIssueCounts.errors} errors`}
                            color={ruleIssueCounts.errors ? "error" : "default"}
                            size="small"
                          />
                          <Chip
                            label={`${ruleIssueCounts.warnings} warnings`}
                            color={ruleIssueCounts.warnings ? "warning" : "default"}
                            size="small"
                          />
                        </Stack>
                        <Button
                          size="small"
                          onClick={() =>
                            setExpandedRuleMessageId((current) =>
                              current === message.id ? null : message.id,
                            )
                          }
                        >
                          {isRuleExpanded ? "Hide details" : "Show details"}
                        </Button>
                      </Stack>
                      <Collapse in={isRuleExpanded} timeout="auto" unmountOnExit>
                        <Box sx={{ mt: 1 }}>
                          <RuleCheckPanel result={ruleCheckResult} compact />
                        </Box>
                      </Collapse>
                    </Box>
                  )}
                </Paper>
              </Box>
            );
          })}

          {isLoading && (
            <Stack direction="row" spacing={1} sx={{ alignItems: "center", color: "text.secondary" }}>
              <CircularProgress size={18} />
              <Typography variant="body2">Waiting for response</Typography>
            </Stack>
          )}
        </Stack>
      </Box>

      <Box
        component="form"
        onSubmit={(event) => {
          event.preventDefault();
          void handleSubmit();
        }}
        sx={{
          flexShrink: 0,
          borderTop: 1,
          borderColor: "divider",
          bgcolor: "background.paper",
          px: { xs: 1.5, md: 3 },
          py: 1.5,
        }}
      >
        <Stack direction="row" spacing={1} sx={{ maxWidth: 980, mx: "auto", alignItems: "flex-end" }}>
          <TranscriptUpload
            ensureSession={ensureSession}
            onUploaded={handleTranscriptUploaded}
            onError={showError}
            disabled={isLoading}
          />
          <TextField
            fullWidth
            multiline
            minRows={1}
            maxRows={5}
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Message or upload a transcript PDF"
            disabled={isLoading}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void handleSubmit();
              }
            }}
          />
          <Tooltip title="Send">
            <span>
              <IconButton
                type="submit"
                color="primary"
                disabled={!canSend}
                aria-label="Send message"
                sx={{ width: 48, height: 48 }}
              >
                <SendOutlinedIcon />
              </IconButton>
            </span>
          </Tooltip>
        </Stack>
        <Stack
          component="aside"
          aria-label="Unofficial service notice"
          direction="row"
          spacing={0.75}
          sx={{
            maxWidth: 980,
            mx: "auto",
            mt: 1,
            alignItems: "flex-start",
            justifyContent: "center",
            color: "text.secondary",
          }}
        >
          <InfoOutlinedIcon sx={{ mt: "1px", fontSize: 16, flexShrink: 0 }} />
          <Typography variant="caption" sx={{ display: { xs: "block", sm: "none" } }}>
            Unofficial service. Please verify important information.
          </Typography>
          <Typography variant="caption" sx={{ display: { xs: "none", sm: "block" } }}>
            Unofficial service. Answers may be incomplete or incorrect. Please verify important
            information using official FU Berlin regulations or the responsible advising office.
          </Typography>
        </Stack>
      </Box>
      <ChatErrorDialog
        open={errorDialogOpen}
        message={error ?? DEFAULT_CHAT_ERROR_MESSAGE}
        onClose={() => {
          setErrorDialogOpen(false);
          setError(null);
        }}
      />
    </Box>
  );
}
