import type {
  Citation,
  MessageType,
  RuleCheckResult,
  StudyPlan,
  TranscriptUploadResponse,
} from "@/types/api";

import { CHAT_MESSAGES_STORAGE_KEY } from "./storage";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  messageType?: MessageType;
  citations?: Citation[];
  ruleCheckResult?: RuleCheckResult | null;
  parsedStudyPlan?: StudyPlan | null;
};

export function createMessageId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function loadStoredChatMessages(): ChatMessage[] {
  if (typeof window === "undefined") {
    return [];
  }

  const stored = window.sessionStorage.getItem(CHAT_MESSAGES_STORAGE_KEY);
  if (!stored) {
    return [];
  }

  try {
    const parsed = JSON.parse(stored);
    if (!Array.isArray(parsed)) {
      return [];
    }

    const messages = parsed.filter(
      (message): message is ChatMessage =>
        typeof message === "object" &&
        message !== null &&
        !String((message as { id?: unknown }).id ?? "").startsWith("dummy-"),
    );
    if (messages.length !== parsed.length) {
      window.sessionStorage.setItem(CHAT_MESSAGES_STORAGE_KEY, JSON.stringify(messages));
    }
    return messages;
  } catch {
    return [];
  }
}

export function appendStoredChatMessages(messages: ChatMessage[]): void {
  if (typeof window === "undefined") {
    return;
  }

  const existing = loadStoredChatMessages();
  window.sessionStorage.setItem(
    CHAT_MESSAGES_STORAGE_KEY,
    JSON.stringify([...existing, ...messages]),
  );
}

/** Turn a transcript-upload result into the user+assistant pair shown in chat. */
export function buildTranscriptChatMessages(
  result: TranscriptUploadResponse,
): ChatMessage[] {
  return [
    {
      id: createMessageId(),
      role: "user",
      content: `Uploaded transcript: ${result.filename}`,
    },
    {
      id: createMessageId(),
      role: "assistant",
      content: result.reply,
      messageType: result.message_type,
      citations: [],
      ruleCheckResult: result.rule_check_result,
      parsedStudyPlan: result.parsed_study_plan,
    },
  ];
}
