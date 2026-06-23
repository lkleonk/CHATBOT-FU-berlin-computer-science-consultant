export type MessageType = "degree_question" | "course_offering_question" | "plan_check" | "off_topic";

export type Citation = {
  source: string;
  title: string | null;
  section_heading: string | null;
  page: number | null;
  score: number | null;
};

export type RuleIssue = {
  code: string;
  severity: "error" | "warning";
  message: string;
  details: Record<string, unknown>;
};

export type RuleCheckResult = {
  is_valid: boolean;
  summary: string;
  totals: Record<string, number>;
  issues: RuleIssue[];
};

export type ModuleArea =
  | "practical"
  | "theoretical"
  | "technical"
  | "application"
  | "thesis"
  | "unknown";

export type SpecializationArea = "practical" | "theoretical" | "technical";

export type PlannedModule = {
  name: string;
  lp: number;
  area: ModuleArea;
  is_wahlbereich: boolean;
  is_ungraded: boolean;
  is_bachelor_module: boolean;
  is_scientific_work: boolean;
  is_software_project: boolean;
};

export type StudyPlan = {
  specialization_area: SpecializationArea | null;
  modules: PlannedModule[];
};

export type ModelReply = {
  reply: string;
  message_type: MessageType;
  citations: Citation[];
  rule_check_result: RuleCheckResult | null;
  parsed_study_plan: StudyPlan | null;
};

export type TranscriptUploadResponse = {
  filename: string;
  message_type: "plan_check";
  reply: string;
  parsed_study_plan: StudyPlan | null;
  rule_check_result: RuleCheckResult | null;
};

export type ApiErrorDetail = {
  error_code?: string;
  message?: string;
  limit?: number;
  remaining?: number;
  reset_at?: string;
  readability?: Record<string, unknown>;
};

export type UsageQuota = {
  limit: number;
  used: number;
  remaining: number;
  reset_at: string;
};

export type UsageResponse = UsageQuota & {
  session_inactivity_ttl_seconds: number;
  diagnostic_tracing_enabled: boolean;
  quota_scope: "client_ip";
};

export type QuotaAwareResponse<T> = {
  data: T;
  usage: UsageQuota | null;
};

export type SessionResponse = {
  session_id: string;
};

export type HealthResponse = {
  status: "healthy" | "degraded";
  services: Record<string, string>;
};

export type ProgramRuleSource = {
  label: string;
  path: string;
  note: string | null;
};

export type ProgramRuleItem = {
  label: string;
  text: string;
  minimum: number | null;
  maximum: number | null;
  unit: string | null;
};

export type ProgramRuleSection = {
  id: string;
  title: string;
  description: string;
  items: ProgramRuleItem[];
  related_issue_codes: string[];
  sources: ProgramRuleSource[];
};

export type ProgramRulesCatalogue = {
  degree_program: string;
  regulation: string;
  catalogue_version: string;
  source_note: string;
  sections: ProgramRuleSection[];
};
