"""Declarative catalogue of research-agent skills."""
from dataclasses import dataclass

@dataclass(frozen=True)
class ResearchSkill:
    key: str
    name: str
    purpose: str

RESEARCH_SKILLS = (
    ResearchSkill("research-question", "Research Question", "Formulate focused, answerable research questions."),
    ResearchSkill("research-gap", "Research Gap", "Identify gaps supported by reviewed literature."),
    ResearchSkill("novelty-detection", "Novelty Assessment", "Compare claimed contributions against available evidence."),
    ResearchSkill("literature-search", "Literature Search", "Plan reproducible searches across configured scholarly sources."),
    ResearchSkill("critical-appraisal", "Critical Appraisal", "Assess study quality, bias, and limitations."),
    ResearchSkill("systematic-review", "Systematic Review", "Structure screening, eligibility, extraction, and synthesis."),
    ResearchSkill("bibliometric-analysis", "Bibliometric Analysis", "Specify bibliometric indicators and network-analysis workflows."),
    ResearchSkill("journal-ranking", "Journal Quality", "Verify journal standing against authoritative indexing sources."),
    ResearchSkill("journal-matching", "Journal Matching", "Match manuscript scope to journal aims and author guidance."),
    ResearchSkill("research-methodology", "Research Methodology", "Design methods, sampling, instruments, and validity checks."),
    ResearchSkill("statistical-analysis", "Statistical Analysis", "Select and interpret procedures with assumptions stated."),
    ResearchSkill("qualitative-analysis", "Qualitative Analysis", "Plan coding, thematic analysis, and audit trails."),
    ResearchSkill("academic-writing", "Academic Writing", "Improve structure, clarity, and discipline-appropriate style."),
    ResearchSkill("citation-management", "Citation Management", "Normalize references and verify DOI/metadata."),
    ResearchSkill("plagiarism-audit", "Similarity Audit", "Flag attribution and paraphrase risks without inventing detector scores."),
    ResearchSkill("publication-strategy", "Publication Strategy", "Plan ethical submission and publication sequencing."),
    ResearchSkill("peer-review-response", "Peer Review Response", "Draft evidence-linked responses to reviewer comments."),
    ResearchSkill("research-ethics", "Research Ethics", "Identify consent, privacy, authorship, and approval requirements."),
    ResearchSkill("thesis-assistant", "Thesis Assistant", "Support thesis planning, chapter structure, and consistency checks."),
    ResearchSkill("research-data-validation", "Research Data Validation", "Check schemas, missingness, ranges, and reproducibility metadata."),
)
SKILLS_BY_KEY = {skill.key: skill for skill in RESEARCH_SKILLS}
