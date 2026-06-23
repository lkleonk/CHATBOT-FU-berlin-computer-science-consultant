import type { ChatMessage } from "./chatMessages";
import { loadStoredChatMessages } from "./chatMessages";

function renderMessage(message: ChatMessage): string {
  const lines = [`## ${message.role === "user" ? "You" : "Assistant"}`, "", message.content];

  if (message.citations?.length) {
    lines.push("", "### Sources", "");
    for (const citation of message.citations) {
      const location = [citation.section_heading, citation.page ? `page ${citation.page}` : null]
        .filter(Boolean)
        .join(", ");
      lines.push(`- ${citation.title ?? citation.source}${location ? ` (${location})` : ""}: ${citation.source}`);
    }
  }

  if (message.ruleCheckResult) {
    lines.push("", "### Rule check", "", message.ruleCheckResult.summary);
    if (message.ruleCheckResult.issues.length) {
      lines.push("");
      for (const issue of message.ruleCheckResult.issues) {
        lines.push(`- **${issue.severity.toUpperCase()} — ${issue.code}:** ${issue.message}`);
      }
    }
  }

  return lines.join("\n");
}

export function buildChatMarkdown(messages: ChatMessage[]): string {
  return [
    "# Modulio chat",
    "",
    `Exported: ${new Date().toLocaleString()}`,
    "",
    "> Unofficial service. Answers may be incomplete or incorrect. Verify important information using official FU Berlin sources.",
    "",
    "> Uploaded original PDF files and their extracted raw text are not included in this export.",
    "",
    ...messages.flatMap((message, index) => [renderMessage(message), ...(index < messages.length - 1 ? ["", "---", ""] : [])]),
    "",
  ].join("\n");
}

export function downloadChat(messages: ChatMessage[]): boolean {
  if (messages.length === 0 || typeof window === "undefined") {
    return false;
  }

  const blob = new Blob([buildChatMarkdown(messages)], { type: "text/markdown;charset=utf-8" });
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `fu-cs-consultant-chat-${new Date().toISOString().slice(0, 10)}.md`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(url);
  return true;
}

export function downloadStoredChat(): boolean {
  return downloadChat(loadStoredChatMessages());
}
