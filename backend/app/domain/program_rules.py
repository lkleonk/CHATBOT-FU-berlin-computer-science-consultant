from pydantic import BaseModel, Field


class ProgramRuleSource(BaseModel):
    label: str
    path: str
    note: str | None = None


class ProgramRuleItem(BaseModel):
    label: str
    text: str
    minimum: int | None = None
    maximum: int | None = None
    unit: str | None = None


class ProgramRuleSection(BaseModel):
    id: str
    title: str
    description: str
    items: list[ProgramRuleItem] = Field(default_factory=list)
    related_issue_codes: list[str] = Field(default_factory=list)
    sources: list[ProgramRuleSource] = Field(default_factory=list)


class ProgramRulesCatalogue(BaseModel):
    degree_program: str
    regulation: str
    catalogue_version: str
    source_note: str
    sections: list[ProgramRuleSection]


def render_rules_context(catalogue: ProgramRulesCatalogue) -> str:
    """Render a structured rule catalogue for LLM prompts.

    The structured catalogue remains the source of human-readable rule text.
    This renderer provides a compact prompt projection so the Degree Rules tab
    and user-facing answer composer do not drift apart.
    """

    lines = [
        f"{catalogue.degree_program} - {catalogue.regulation}",
        "",
        catalogue.source_note,
    ]

    for section in catalogue.sections:
        lines.extend(["", section.title.upper(), f"- {section.description}"])
        for item in section.items:
            lines.append(f"- {item.label}: {item.text}")
        for source in section.sources:
            if source.path.startswith("http"):
                lines.append(f"- Official source: [{source.label}]({source.path})")

    return "\n".join(lines).strip()
