export interface FormatFlag {
  issue: string;
  severity: "high" | "medium" | "low" | string;
}

export interface ReportResult {
  match_score: number;
  missing_required_skills: string[];
  missing_nice_to_have: string[];
  matched_skills: string[];
  suggestions: string[];
  format_flags: FormatFlag[];
  jd_analysis?: {
    required_skills: string[];
    nice_to_have_skills: string[];
    years_experience: string;
    keywords: string[];
  };
  resume_sections?: Record<string, unknown>;
}
