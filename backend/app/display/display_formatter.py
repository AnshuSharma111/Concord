from typing import List, Optional
from .display_model import (
    BehaviorUnitCard, AssertionInfo, EndpointSummary, 
    RiskDrivenView, CoverageView, DisplayContext, RiskBand
)
from analysis.analysis_model import FindingKind
from claims.claim_model import ArtifactSource

# -------------------------Formatting Constants-------------------------------------

# Tier 2 finding symbols and labels
FINDING_SYMBOLS = {
    FindingKind.CONTRADICTION: "🔴",
    FindingKind.DOCUMENTATION_ONLY: "🟡", 
    FindingKind.IMPLEMENTATION_ONLY: "🟠",
    FindingKind.UNVERIFIED: "🟤",
    FindingKind.MULTIPLE_SUCCESS_VARIANTS: "🟣"
}

FINDING_LABELS = {
    FindingKind.CONTRADICTION: "CONTRADICTION",
    FindingKind.DOCUMENTATION_ONLY: "DOCUMENTATION_ONLY",
    FindingKind.IMPLEMENTATION_ONLY: "IMPLEMENTATION_ONLY", 
    FindingKind.UNVERIFIED: "UNVERIFIED",
    FindingKind.MULTIPLE_SUCCESS_VARIANTS: "MULTIPLE_SUCCESS_VARIANTS"
}

# Risk band symbols
RISK_SYMBOLS = {
    RiskBand.CRITICAL: "🔴",
    RiskBand.HIGH: "🟠", 
    RiskBand.MEDIUM: "🟡",
    RiskBand.LOW: "🟢"
}

# Source abbreviations
SOURCE_ABBREV = {
    ArtifactSource.TEST: "TEST",
    ArtifactSource.API_SPEC: "API_SPEC",
    ArtifactSource.README: "README"
}

# -------------------------Canonical Unit Card Formatting-------------------------------------

def format_condition(condition: Optional[str]) -> str:
    """Format condition with fallback to em dash."""
    return condition if condition else "—"

def format_assertion_info(assertion_info: AssertionInfo, has_conflicts: bool) -> str:
    """Format single assertion with agreement indicator and sources."""
    # Agreement indicator
    indicator = "❌" if (has_conflicts and assertion_info.is_conflicted) else "✅"
    
    # Source list
    source_list = ", ".join(sorted(SOURCE_ABBREV[s] for s in assertion_info.sources))
    
    return f"{indicator} {assertion_info.assertion} — {source_list}"

def format_assertions_block(unit_card: BehaviorUnitCard) -> List[str]:
    """Format all assertions for a unit card."""
    assertions = []
    
    for assertion_info in unit_card.assertion_state.assertions:
        formatted = format_assertion_info(assertion_info, unit_card.assertion_state.has_conflicts)
        assertions.append(formatted)
    
    return assertions

def format_findings_block(unit_card: BehaviorUnitCard) -> List[str]:
    """Format structural warnings (Tier 2 findings only)."""
    findings = []
    
    for finding_kind in unit_card.structural_warnings:
        symbol = FINDING_SYMBOLS.get(finding_kind, "⚪")
        label = FINDING_LABELS.get(finding_kind, finding_kind.value.upper())
        findings.append(f"{symbol} {label}")
    
    return findings

def format_context_block(unit_card: BehaviorUnitCard, show_context: bool = False) -> List[str]:
    """Format Tier 3 heuristic context (collapsed by default)."""
    if not show_context:
        return ["Context: [Click to expand]"]
    
    context = []
    if unit_card.coverage_score is not None:
        context.append(f"Coverage: {unit_card.coverage_score:.2f}")
    if unit_card.confidence_score is not None:
        context.append(f"Confidence: {unit_card.confidence_score:.2f}")  
    if unit_card.risk_band is not None:
        context.append(f"Risk: {unit_card.risk_band.value.title()}")
    
    return context

def format_canonical_unit_card(unit_card: BehaviorUnitCard, show_context: bool = False) -> str:
    """Format the canonical unit card exactly as specified."""
    
    lines = []
    
    # Header
    lines.append(f"{unit_card.endpoint}")
    lines.append(f"Condition: {format_condition(unit_card.condition)}")
    lines.append("")
    
    # Assertions (Tier 1)
    lines.append("Assertions")
    assertion_lines = format_assertions_block(unit_card)
    for assertion_line in assertion_lines:
        lines.append(f"  {assertion_line}")
    lines.append("")
    
    # Findings (Tier 2 - only when present)
    if unit_card.structural_warnings:
        lines.append("Findings")
        finding_lines = format_findings_block(unit_card)
        for finding_line in finding_lines:
            lines.append(f"  {finding_line}")
        lines.append("")
    
    # Context (Tier 3 - collapsed by default)
    context_lines = format_context_block(unit_card, show_context)
    for context_line in context_lines:
        lines.append(f"  {context_line}")
    
    return "\n".join(lines)

# -------------------------Aggregated View Formatting-------------------------------------

def format_endpoint_summary(summary: EndpointSummary) -> str:
    """Format endpoint summary view."""
    lines = []
    
    lines.append(f"📡 {summary.endpoint}")
    lines.append(f"   Behaviors: {summary.behavior_count}")
    
    if summary.contradiction_count > 0:
        lines.append(f"   Contradictions: {summary.contradiction_count}")
    
    if summary.undocumented_count > 0:  
        lines.append(f"   Undocumented: {summary.undocumented_count}")
    
    if summary.highest_risk_band:
        symbol = RISK_SYMBOLS.get(summary.highest_risk_band, "")
        lines.append(f"   Risk: {symbol} {summary.highest_risk_band.value.title()}")
    
    return "\n".join(lines)

def format_risk_section(title: str, units: List[BehaviorUnitCard]) -> List[str]:
    """Format a risk-level section."""
    if not units:
        return []
    
    lines = []
    lines.append(f"\n{title} ({len(units)})")
    lines.append("-" * len(f"{title} ({len(units)})"))
    
    for unit in units:
        # Brief one-liner for risk view
        condition_part = f" | {unit.condition}" if unit.condition else ""
        contradiction_marker = " ⚠️" if FindingKind.CONTRADICTION in unit.structural_warnings else ""
        lines.append(f"  {unit.endpoint}{condition_part}{contradiction_marker}")
    
    return lines

def format_risk_driven_view(risk_view: RiskDrivenView) -> str:
    """Format complete risk-driven view."""
    lines = ["🚨 Risk-Driven Priority View"]
    lines.append("=" * 30)
    
    lines.extend(format_risk_section("CRITICAL", risk_view.critical_behaviors))
    lines.extend(format_risk_section("HIGH RISK", risk_view.high_risk_behaviors))
    lines.extend(format_risk_section("MEDIUM RISK", risk_view.medium_risk_behaviors))
    lines.extend(format_risk_section("LOW RISK", risk_view.low_risk_behaviors))
    
    return "\n".join(lines)

def format_coverage_section(title: str, units: List[BehaviorUnitCard]) -> List[str]:
    """Format a coverage gap section."""
    if not units:
        return []
    
    lines = []
    lines.append(f"\n{title} ({len(units)})")
    lines.append("-" * len(f"{title} ({len(units)})"))
    
    for unit in units:
        condition_part = f" | {unit.condition}" if unit.condition else ""
        lines.append(f"  {unit.endpoint}{condition_part}")
    
    return lines

def format_coverage_view(coverage_view: CoverageView) -> str:
    """Format complete coverage view."""
    lines = ["📊 Coverage Gap Analysis"]
    lines.append("=" * 25)
    
    lines.extend(format_coverage_section("NO TESTS", coverage_view.no_tests))
    lines.extend(format_coverage_section("NO API SPEC", coverage_view.no_spec))  
    lines.extend(format_coverage_section("NO README", coverage_view.no_readme))
    lines.extend(format_coverage_section("FULL COVERAGE", coverage_view.full_coverage))
    
    return "\n".join(lines)

def format_display_summary(display_context: DisplayContext) -> str:
    """Format high-level summary statistics."""
    lines = []
    lines.append(f"📋 Total Behaviors: {display_context.total_behaviors()}")
    lines.append(f"⚠️  Total Contradictions: {display_context.total_contradictions()}")
    lines.append(f"📡 Unique Endpoints: {len(display_context.endpoint_summaries)}")
    
    # Risk distribution
    risk_counts = {
        RiskBand.CRITICAL: len(display_context.risk_driven_view.critical_behaviors),
        RiskBand.HIGH: len(display_context.risk_driven_view.high_risk_behaviors),
        RiskBand.MEDIUM: len(display_context.risk_driven_view.medium_risk_behaviors), 
        RiskBand.LOW: len(display_context.risk_driven_view.low_risk_behaviors)
    }
    
    lines.append("")
    lines.append("Risk Distribution:")
    for risk_band, count in risk_counts.items():
        if count > 0:
            symbol = RISK_SYMBOLS.get(risk_band, "")
            lines.append(f"  {symbol} {risk_band.value.title()}: {count}")
    
    return "\n".join(lines)

# -------------------------Complete Display Formatter-------------------------------------

def format_complete_display(display_context: DisplayContext, show_context: bool = False) -> str:
    """Format complete display with all three tiers."""
    
    sections = []
    
    # Summary
    sections.append(format_display_summary(display_context))
    sections.append("")
    
    # Individual unit cards
    sections.append("📝 Behavioral Units")
    sections.append("=" * 20)
    for i, unit in enumerate(display_context.behavioral_units):
        sections.append(f"\n[{i+1}] " + "=" * 40)
        sections.append(format_canonical_unit_card(unit, show_context))
    
    sections.append("\n" + "=" * 60)
    
    # Aggregated views  
    sections.append(format_risk_driven_view(display_context.risk_driven_view))
    sections.append("")
    sections.append(format_coverage_view(display_context.coverage_view))
    
    return "\n".join(sections)