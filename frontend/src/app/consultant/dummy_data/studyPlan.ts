import type { StudyPlan } from "@/types/api";

/**
 * Partial frontend-only extract from Leistungsuebersicht_Max_Mustermann_Demo.pdf.
 * This is a developer preview, not a complete transcript or rule-check result.
 */
export const STUDY_PLAN_DUMMY_DATA: Record<string, StudyPlan> = {
  msc_informatik: {
    specialization_area: "practical",
    modules: [
      {
        name: "Künstliche Intelligenz",
        lp: 5,
        area: "practical",
        is_wahlbereich: false,
        is_ungraded: false,
        is_bachelor_module: false,
        is_scientific_work: false,
        is_software_project: false,
      },
      {
        name: "Rechnersicherheit",
        lp: 10,
        area: "practical",
        is_wahlbereich: false,
        is_ungraded: false,
        is_bachelor_module: false,
        is_scientific_work: false,
        is_software_project: false,
      },
      {
        name: "Softwareprojekt Praktische Informatik A",
        lp: 10,
        area: "practical",
        is_wahlbereich: false,
        is_ungraded: false,
        is_bachelor_module: false,
        is_scientific_work: false,
        is_software_project: true,
      },
      {
        name: "Wissenschaftliches Arbeiten Theoretische Informatik A",
        lp: 5,
        area: "theoretical",
        is_wahlbereich: false,
        is_ungraded: true,
        is_bachelor_module: false,
        is_scientific_work: true,
        is_software_project: false,
      },
      {
        name: "Anwendungsmodul Betriebswirtschaftslehre A",
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
  },
};

export function getDummyStudyPlan(degreeId: string): StudyPlan | null {
  return STUDY_PLAN_DUMMY_DATA[degreeId] ?? null;
}
