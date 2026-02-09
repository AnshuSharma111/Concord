"""
Debug logging system for semantic analysis pipeline.

Captures the complete processing pipeline from file names through validation,
evidence generation, claims, analysis, evaluation, and final results.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Union, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from contextlib import contextmanager

# Models for type hints
from evidence.evidence_model import Evidence  
from claims.claim_model import Claim
from analysis.analysis_model import AnalysisObject, EvaluationObject
from display.display_model import DisplayContext


@dataclass
class ProcessingStep:
    """Single step in the processing pipeline."""
    stage: str
    timestamp: str
    duration_ms: int
    input_count: int
    output_count: int
    details: Dict[str, Any]
    errors: List[str]


class ProcessLogger:
    """Comprehensive logging for the semantic analysis pipeline."""
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize logger with an optional session ID.
        
        Args:
            session_id: Unique identifier for this analysis session
        """
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        self.start_time = datetime.now()
        self.steps: List[ProcessingStep] = []
        self.current_step_start: Optional[datetime] = None
        self.debug_dir = Path(__file__).parent.parent / "debug"  # backend/debug/ directory
        self.debug_dir.mkdir(exist_ok=True)
        self.log_file = self.debug_dir / f"process_log_{self.session_id}.txt"
        
        # Initialize log file
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"=== CONCORD SEMANTIC ANALYSIS DEBUG LOG ===\n")
            f.write(f"Session ID: {self.session_id}\n")
            f.write(f"Start Time: {self.start_time.isoformat()}\n")
            f.write(f"{'='*80}\n\n")
    
    @contextmanager
    def stage(self, stage_name: str, details: Optional[Dict[str, Any]] = None):
        """
        Context manager for logging a processing stage.
        
        Args:
            stage_name: Name of the processing stage
            details: Additional details about the stage
        """
        stage_start = datetime.now()
        self.current_step_start = stage_start
        
        self._log_message(f"🚀 Starting Stage: {stage_name}")
        if details:
            self._log_details("Stage Details", details)
        
        input_count = 0
        output_count = 0
        errors = []
        stage_details = details or {}
        
        try:
            # Create stage context object
            stage_context = StageContext(self, stage_name, stage_details)
            yield stage_context
            
            input_count = stage_context.input_count
            output_count = stage_context.output_count
            errors = stage_context.errors
            stage_details.update(stage_context.details)
            
        except Exception as e:
            errors.append(f"Stage failed: {str(e)}")
            self._log_message(f"❌ Stage Failed: {stage_name} - {str(e)}")
            raise
        finally:
            # Calculate duration
            duration = datetime.now() - stage_start
            duration_ms = int(duration.total_seconds() * 1000)
            
            # Record the step
            step = ProcessingStep(
                stage=stage_name,
                timestamp=stage_start.isoformat(),
                duration_ms=duration_ms,
                input_count=input_count,
                output_count=output_count,
                details=stage_details,
                errors=errors
            )
            self.steps.append(step)
            
            # Log completion
            status = "❌" if errors else "✅"
            self._log_message(f"{status} Completed Stage: {stage_name} ({duration_ms}ms)")
            self._log_message(f"   Input: {input_count} | Output: {output_count} | Errors: {len(errors)}")
            if errors:
                for error in errors:
                    self._log_message(f"   Error: {error}")
            self._log_message("")
    
    def log_file_inputs(self, file_paths: List[Union[str, Path]], detected_types: Dict[str, str]):
        """
        Log input files and their detected types.
        
        Args:
            file_paths: List of input file paths
            detected_types: Mapping of file paths to detected types
        """
        self._log_message("📁 Input Files:")
        for file_path in file_paths:
            file_path_str = str(file_path)
            file_type = detected_types.get(file_path_str, "UNKNOWN")
            file_size = "unknown"
            
            try:
                if Path(file_path).exists():
                    file_size = f"{Path(file_path).stat().st_size} bytes"
            except:
                pass
                
            self._log_message(f"   📄 {Path(file_path).name} ({file_type}) - {file_size}")
            self._log_message(f"      Path: {file_path}")
        self._log_message("")
    
    def log_evidence_details(self, evidence_list: List[Evidence]):
        """Log detailed evidence information."""
        if not evidence_list:
            self._log_message("   No evidence extracted.")
            return
            
        self._log_message(f"   Evidence Summary: {len(evidence_list)} items")
        
        # Group by source type
        by_source = {}
        for evidence in evidence_list:
            source = evidence.type.value if hasattr(evidence.type, 'value') else str(evidence.type)
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(evidence)
        
        for source, items in by_source.items():
            self._log_message(f"      {source}: {len(items)} items")
            for item in items[:3]:  # Show first 3 items
                self._log_message(f"         - {item.observation[:100]}...")
            if len(items) > 3:
                self._log_message(f"         ... and {len(items) - 3} more")
    
    def log_claims_details(self, claims: List[Claim], rejections: Optional[List] = None):
        """Log detailed claims information."""
        self._log_message(f"   Claims Generated: {len(claims)}")
        if rejections:
            self._log_message(f"   Claims Rejected: {len(rejections)}")
        
        for i, claim in enumerate(claims[:5]):  # Show first 5 claims
            self._log_message(f"      Claim {i+1}: {claim.endpoint}")
            self._log_message(f"         Source: {claim.source.value}")
            self._log_message(f"         Assertion: {claim.assertion}")
        
        if len(claims) > 5:
            self._log_message(f"      ... and {len(claims) - 5} more claims")
    
    def log_analysis_details(self, analyses: List[AnalysisObject]):
        """Log detailed analysis information."""
        self._log_message(f"   Analyses Created: {len(analyses)}")
        
        for i, analysis in enumerate(analyses[:3]):  # Show first 3 analyses
            findings_count = len(analysis.findings) if analysis.findings else 0
            claims_count = len(analysis.claims) if analysis.claims else 0
            self._log_message(f"      Analysis {i+1}: {claims_count} claims, {findings_count} findings")
        
        if len(analyses) > 3:
            self._log_message(f"      ... and {len(analyses) - 3} more analyses")
    
    def log_evaluation_details(self, evaluations: List[EvaluationObject]):
        """Log detailed evaluation information.""" 
        self._log_message(f"   Evaluations Created: {len(evaluations)}")
        
        total_critical = sum(1 for e in evaluations if e.risk_level == 'critical')
        total_high = sum(1 for e in evaluations if e.risk_level == 'high')
        total_medium = sum(1 for e in evaluations if e.risk_level == 'medium')
        total_low = sum(1 for e in evaluations if e.risk_level == 'low')
        
        self._log_message(f"      Risk Distribution: Critical={total_critical}, High={total_high}, Medium={total_medium}, Low={total_low}")
    
    def log_display_context_details(self, display_context: DisplayContext):
        """Log final display context details."""
        self._log_message("   Display Context Summary:")
        
        units_count = len(display_context.behavioral_units)
        self._log_message(f"      Behavioral Units: {units_count}")
        
        contradictions = sum(1 for unit in display_context.behavioral_units 
                           if unit.assertion_state.has_conflicts)
        self._log_message(f"      Contradictions Found: {contradictions}")
        
        total_behaviors = display_context.total_behaviors()
        total_contradictions = display_context.total_contradictions()
        self._log_message(f"      Total Behaviors: {total_behaviors}")
        self._log_message(f"      Total Contradictions: {total_contradictions}")
    
    def finalize_log(self, final_result: Any):
        """Write final summary and close the log."""
        total_duration = datetime.now() - self.start_time
        total_duration_ms = int(total_duration.total_seconds() * 1000)
        
        self._log_message("🏁 PROCESSING COMPLETE")
        self._log_message(f"Total Duration: {total_duration_ms}ms ({total_duration.total_seconds():.2f}s)")
        self._log_message(f"Total Stages: {len(self.steps)}")
        
        # Summary statistics
        total_errors = sum(len(step.errors) for step in self.steps)
        if total_errors > 0:
            self._log_message(f"❌ Total Errors: {total_errors}")
        else:
            self._log_message("✅ No errors encountered")
        
        self._log_message("\n" + "="*80)
        self._log_message("FINAL PROCESSING SUMMARY")
        self._log_message("="*80)
        
        for step in self.steps:
            status = "❌" if step.errors else "✅"
            self._log_message(f"{status} {step.stage}: {step.input_count}→{step.output_count} ({step.duration_ms}ms)")
        
        # Write JSON summary
        self._write_json_summary(final_result, total_duration_ms)
        
        self._log_message(f"\nDebug log saved to: {self.log_file}")
        self._log_message(f"JSON summary saved to: {self.log_file.with_suffix('.json')}")
    
    def _log_message(self, message: str):
        """Write a message to the log file.""" 
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
    
    def _log_details(self, title: str, details: Dict[str, Any]):
        """Log detailed information in a structured format."""
        self._log_message(f"{title}:")
        for key, value in details.items():
            if isinstance(value, (list, dict)):
                self._log_message(f"   {key}: {json.dumps(value, indent=2, default=str)}")
            else:
                self._log_message(f"   {key}: {value}")
    
    def _write_json_summary(self, final_result: Any, total_duration_ms: int):
        """Write a JSON summary of the processing session."""
        summary = {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "total_duration_ms": total_duration_ms,
            "steps": [
                {
                    "stage": step.stage,
                    "timestamp": step.timestamp,
                    "duration_ms": step.duration_ms,
                    "input_count": step.input_count,
                    "output_count": step.output_count,
                    "details": step.details,
                    "errors": step.errors,
                    "success": len(step.errors) == 0
                }
                for step in self.steps
            ],
            "total_errors": sum(len(step.errors) for step in self.steps),
            "success": all(len(step.errors) == 0 for step in self.steps)
        }
        
        json_file = self.log_file.with_suffix('.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, default=str, ensure_ascii=False)


class StageContext:
    """Context object for a processing stage."""
    
    def __init__(self, logger: ProcessLogger, stage_name: str, initial_details: Dict[str, Any]):
        self.logger = logger
        self.stage_name = stage_name
        self.details = initial_details.copy()
        self.input_count = 0
        self.output_count = 0
        self.errors: List[str] = []
    
    def set_input_count(self, count: int):
        """Set the input count for this stage."""
        self.input_count = count
        self.logger._log_message(f"   📥 Input Count: {count}")
    
    def set_output_count(self, count: int):
        """Set the output count for this stage."""
        self.output_count = count
        self.logger._log_message(f"   📤 Output Count: {count}")
    
    def add_detail(self, key: str, value: Any):
        """Add a detail to this stage."""
        self.details[key] = value
        self.logger._log_message(f"   ℹ️  {key}: {value}")
    
    def add_error(self, error: str):
        """Add an error to this stage."""
        self.errors.append(error)
        self.logger._log_message(f"   ❌ Error: {error}")
    
    def log_message(self, message: str):
        """Log a message for this stage."""
        self.logger._log_message(f"   {message}")