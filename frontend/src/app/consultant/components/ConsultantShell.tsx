"use client";

import ChatBubbleOutlineIcon from "@mui/icons-material/ChatBubbleOutlineOutlined";
import FactCheckOutlinedIcon from "@mui/icons-material/FactCheckOutlined";
import RuleOutlinedIcon from "@mui/icons-material/RuleOutlined";
import SchoolOutlinedIcon from "@mui/icons-material/SchoolOutlined";
import SettingsOutlinedIcon from "@mui/icons-material/SettingsOutlined";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import Typography from "@mui/material/Typography";
import { useEffect, useState } from "react";

import type { Citation, MessageType, RuleCheckResult, StudyPlan } from "@/types/api";

import { ChatTab } from "./ChatTab";
import { DegreeRulesTab } from "./DegreeRulesTab";
import { SettingsTab } from "./SettingsTab";
import { StudyPlanTab } from "./StudyPlanTab";
import { CHAT_MESSAGES_STORAGE_KEY, SESSION_ID_STORAGE_KEY } from "./storage";

const tabs = [
  { label: "Chat", icon: <ChatBubbleOutlineIcon />, id: "chat" },
  { label: "Study Plan", icon: <FactCheckOutlinedIcon />, id: "study-plan" },
  { label: "Degree Rules", icon: <RuleOutlinedIcon />, id: "degree-rules" },
  { label: "Settings", icon: <SettingsOutlinedIcon />, id: "settings" },
];

type StoredChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  messageType?: MessageType;
  citations?: Citation[];
  ruleCheckResult?: RuleCheckResult | null;
  parsedStudyPlan?: StudyPlan | null;
};

const DUMMY_STUDY_PLAN: StudyPlan = {
  specialization_area: "technical",
  modules: [
    {
      name: "Softwareprojekt Campus Planner B",
      lp: 10,
      area: "practical",
      is_wahlbereich: false,
      is_ungraded: true,
      is_bachelor_module: false,
      is_scientific_work: false,
      is_software_project: true,
    },
    {
      name: "Advanced Software Engineering",
      lp: 10,
      area: "practical",
      is_wahlbereich: false,
      is_ungraded: false,
      is_bachelor_module: false,
      is_scientific_work: false,
      is_software_project: false,
    },
    {
      name: "Advanced Algorithms",
      lp: 10,
      area: "theoretical",
      is_wahlbereich: false,
      is_ungraded: false,
      is_bachelor_module: false,
      is_scientific_work: false,
      is_software_project: false,
    },
    {
      name: "Model Checking",
      lp: 10,
      area: "theoretical",
      is_wahlbereich: false,
      is_ungraded: false,
      is_bachelor_module: false,
      is_scientific_work: false,
      is_software_project: false,
    },
    {
      name: "Wissenschaftliches Arbeiten Theoretische Informatik",
      lp: 5,
      area: "theoretical",
      is_wahlbereich: false,
      is_ungraded: true,
      is_bachelor_module: false,
      is_scientific_work: true,
      is_software_project: false,
    },
    {
      name: "Secure Systems",
      lp: 10,
      area: "technical",
      is_wahlbereich: false,
      is_ungraded: false,
      is_bachelor_module: false,
      is_scientific_work: false,
      is_software_project: false,
    },
    {
      name: "Computer Architecture Lab",
      lp: 10,
      area: "technical",
      is_wahlbereich: false,
      is_ungraded: true,
      is_bachelor_module: false,
      is_scientific_work: false,
      is_software_project: false,
    },
    {
      name: "Machine Learning",
      lp: 10,
      area: "technical",
      is_wahlbereich: false,
      is_ungraded: false,
      is_bachelor_module: false,
      is_scientific_work: false,
      is_software_project: false,
    },
    {
      name: "Wissenschaftliches Arbeiten Technische Informatik",
      lp: 5,
      area: "technical",
      is_wahlbereich: false,
      is_ungraded: true,
      is_bachelor_module: false,
      is_scientific_work: true,
      is_software_project: false,
    },
    {
      name: "Human-Computer Interaction in Education",
      lp: 10,
      area: "application",
      is_wahlbereich: false,
      is_ungraded: false,
      is_bachelor_module: false,
      is_scientific_work: false,
      is_software_project: false,
    },
    {
      name: "Masterarbeit",
      lp: 30,
      area: "thesis",
      is_wahlbereich: false,
      is_ungraded: false,
      is_bachelor_module: false,
      is_scientific_work: false,
      is_software_project: false,
    },
  ],
};

const DUMMY_RULE_CHECK: RuleCheckResult = {
  is_valid: true,
  summary: "Dummy study plan satisfies the implemented 2014 Master Informatik checks.",
  totals: {
    practical_lp: 20,
    theoretical_lp: 25,
    technical_lp: 35,
    application_lp: 10,
    informatics_lp: 80,
    module_area_lp: 90,
    thesis_lp: 30,
    master_total_lp: 120,
    ungraded_lp: 30,
    bachelor_module_lp: 0,
    wahlbereich_lp: 0,
    core_scientific_work_count: 2,
    total_scientific_work_count: 2,
    core_software_project_count: 1,
    total_software_project_count: 1,
  },
  issues: [],
};

function createDummyMessages(): StoredChatMessage[] {
  return [
    {
      id: "dummy-user-study-plan",
      role: "user",
      content: "Load dummy study plan data for frontend testing.",
    },
    {
      id: "dummy-assistant-study-plan",
      role: "assistant",
      content:
        "Dummy data loaded. This is a frontend-only fixture for testing the Study Plan and print/PDF view without the backend.",
      messageType: "plan_check",
      citations: [],
      ruleCheckResult: DUMMY_RULE_CHECK,
      parsedStudyPlan: DUMMY_STUDY_PLAN,
    },
  ];
}

function readStoredSessionId() {
  if (typeof window === "undefined") {
    return null;
  }
  return window.sessionStorage.getItem(SESSION_ID_STORAGE_KEY);
}

function readStoredRuleCheck(): RuleCheckResult | null {
  if (typeof window === "undefined") {
    return null;
  }

  const stored = window.sessionStorage.getItem(CHAT_MESSAGES_STORAGE_KEY);
  if (!stored) {
    return null;
  }

  try {
    const parsed = JSON.parse(stored);
    if (!Array.isArray(parsed)) {
      return null;
    }

    const latest = [...parsed].reverse().find((message) => message?.ruleCheckResult);
    return latest?.ruleCheckResult ?? null;
  } catch {
    return null;
  }
}

function readStoredStudyPlan(): StudyPlan | null {
  if (typeof window === "undefined") {
    return null;
  }

  const stored = window.sessionStorage.getItem(CHAT_MESSAGES_STORAGE_KEY);
  if (!stored) {
    return null;
  }

  try {
    const parsed = JSON.parse(stored);
    if (!Array.isArray(parsed)) {
      return null;
    }

    const latest = [...parsed].reverse().find((message) => message?.parsedStudyPlan);
    return latest?.parsedStudyPlan ?? null;
  } catch {
    return null;
  }
}

export function ConsultantShell() {
  const [activeTab, setActiveTab] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [latestRuleCheck, setLatestRuleCheck] = useState<RuleCheckResult | null>(null);
  const [latestStudyPlan, setLatestStudyPlan] = useState<StudyPlan | null>(null);
  const [resetToken, setResetToken] = useState(0);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setSessionId(readStoredSessionId());
      setLatestRuleCheck(readStoredRuleCheck());
      setLatestStudyPlan(readStoredStudyPlan());
    }, 0);

    return () => window.clearTimeout(timer);
  }, []);

  const handleClearLocalState = () => {
    window.sessionStorage.removeItem(SESSION_ID_STORAGE_KEY);
    window.sessionStorage.removeItem(CHAT_MESSAGES_STORAGE_KEY);
    setSessionId(null);
    setLatestRuleCheck(null);
    setLatestStudyPlan(null);
    setResetToken((current) => current + 1);
    setActiveTab(0);
  };

  const handleLoadDummyData = () => {
    const dummySessionId = "dummy-session";
    window.sessionStorage.setItem(SESSION_ID_STORAGE_KEY, dummySessionId);
    window.sessionStorage.setItem(CHAT_MESSAGES_STORAGE_KEY, JSON.stringify(createDummyMessages()));
    setSessionId(dummySessionId);
    setLatestRuleCheck(DUMMY_RULE_CHECK);
    setLatestStudyPlan(DUMMY_STUDY_PLAN);
    setResetToken((current) => current + 1);
    setActiveTab(1);
  };

  return (
    <Box
      sx={{
        height: "100dvh",
        minHeight: 0,
        display: "flex",
        flexDirection: "column",
        bgcolor: "background.default",
        color: "text.primary",
      }}
    >
      <Box
        component="header"
        data-print-hidden="true"
        sx={{
          flexShrink: 0,
          bgcolor: "background.paper",
          borderBottom: 1,
          borderColor: "divider",
        }}
      >
        <Box
          sx={{
            px: { xs: 1.5, md: 3 },
            py: 1.25,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 1.5,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <SchoolOutlinedIcon color="primary" />
            <Box>
              <Typography variant="h1">FU Berlin CS Consultant</Typography>
              <Typography variant="body2" sx={{ color: "text.secondary" }}>
                Master Informatik
              </Typography>
            </Box>
          </Box>
          <Chip
            label={sessionId ? "Session active" : "No session"}
            color={sessionId ? "success" : "default"}
            size="small"
            sx={{ display: { xs: "none", sm: "inline-flex" } }}
          />
        </Box>
        <Tabs
          value={activeTab}
          onChange={(_, nextTab) => setActiveTab(nextTab)}
          variant="fullWidth"
          sx={{
            minHeight: { xs: 44, sm: 52 },
            px: { xs: 0.5, md: 2 },
          }}
        >
          {tabs.map((tab) => (
            <Tab
              key={tab.id}
              icon={tab.icon}
              iconPosition="start"
              label={
                <Box component="span" sx={{ display: { xs: "none", sm: "inline" } }}>
                  {tab.label}
                </Box>
              }
              id={`${tab.id}-tab`}
              aria-label={tab.label}
              aria-controls={`${tab.id}-panel`}
              sx={{
                minWidth: 0,
                minHeight: { xs: 44, sm: 52 },
                px: { xs: 0.75, sm: 2 },
                "& .MuiTab-iconWrapper": {
                  mr: { xs: 0, sm: 1 },
                },
              }}
            />
          ))}
        </Tabs>
      </Box>

      <Box component="main" sx={{ flex: 1, minHeight: 0 }}>
        <Box
          id="chat-panel"
          role="tabpanel"
          hidden={activeTab !== 0}
          aria-labelledby="chat-tab"
          sx={{ height: "100%", minHeight: 0 }}
        >
          {activeTab === 0 && (
            <ChatTab
              key={resetToken}
              sessionId={sessionId}
              onSessionIdChange={setSessionId}
              onRuleCheckResult={setLatestRuleCheck}
              onStudyPlan={setLatestStudyPlan}
            />
          )}
        </Box>
        <Box
          id="study-plan-panel"
          role="tabpanel"
          hidden={activeTab !== 1}
          aria-labelledby="study-plan-tab"
          sx={{ height: "100%", minHeight: 0 }}
        >
          {activeTab === 1 && (
            <StudyPlanTab
              latestRuleCheck={latestRuleCheck}
              latestStudyPlan={latestStudyPlan}
              sessionId={sessionId}
              onSessionIdChange={setSessionId}
              onRuleCheckResult={setLatestRuleCheck}
              onStudyPlan={setLatestStudyPlan}
            />
          )}
        </Box>
        <Box
          id="degree-rules-panel"
          role="tabpanel"
          hidden={activeTab !== 2}
          aria-labelledby="degree-rules-tab"
          sx={{ height: "100%", minHeight: 0 }}
        >
          {activeTab === 2 && <DegreeRulesTab />}
        </Box>
        <Box
          id="settings-panel"
          role="tabpanel"
          hidden={activeTab !== 3}
          aria-labelledby="settings-tab"
          sx={{ height: "100%", minHeight: 0 }}
        >
          {activeTab === 3 && (
            <SettingsTab
              sessionId={sessionId}
              onClearLocalState={handleClearLocalState}
              onLoadDummyData={handleLoadDummyData}
            />
          )}
        </Box>
      </Box>
    </Box>
  );
}
