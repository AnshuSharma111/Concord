"""
Process orchestration facade for the semantic analysis pipeline.

This module knows exactly one thing: 
"Given a codebase (or artifact set), give me a DisplayContext."

Responsibilities:
- Call each stage in correct order
- Enforce stage boundaries  
- Wire outputs → inputs
- Return display-ready objects only

Does NOT:
- Contain business logic
- Reformat data
- Interpret findings
- Apply policy
- Call Gemini

Think of this as main() for the semantic engine.
"""

from typing import List, Union, Optional
from pathlib import Path
import os
from dataclasses import dataclass

# Pipeline stage imports
from ingest.extract import extract_evidence_from_file
from claims.evidence_to_claim import DeterministicClaimGenerator
from analysis.analysis import analyse_claims
from analysis.evaluation import evaluate_bucket
from display.display_processor import create_display_context

# Debug logging
from debug_logger import ProcessLogger

# Models
from evidence.evidence_model import Evidence
from claims.claim_model import Claim, ArtifactSource
from analysis.analysis_model import AnalysisObject, EvaluationObject
from display.display_model import DisplayContext

@dataclass
class ProcessResult:
    """Result of semantic analysis processing."""
    display_context: DisplayContext
    evidence_count: int
    claims_count: int
    analysis_count: int
    evaluation_count: int

def detect_file_type(file_path: Union[str, Path]) -> Optional[ArtifactSource]:
    """
    Detect artifact source type based on file name and extension patterns.
    
    Args:
        file_path: Path to file
        
    Returns:
        ArtifactSource if detectable, None if not supported
    """
    file_path = Path(file_path)
    filename = file_path.name.lower()
    
    # README files (case insensitive) - check this first before test patterns
    if ('readme' in filename and filename.endswith(('.md', '.txt', '.rst'))) or filename in ['readme.md', 'readme.txt', 'readme.rst', 'readme']:
        return ArtifactSource.README
    
    # API specification files  
    api_spec_patterns = ['openapi', 'swagger', 'api-spec', 'api_spec', 'spec']
    if any(pattern in filename for pattern in api_spec_patterns):
        # If it's a YAML/JSON file with 'spec' in name, likely an API spec
        if file_path.suffix.lower() in ['.yaml', '.yml', '.json']:
            return ArtifactSource.API_SPEC
    elif file_path.suffix.lower() in ['.yaml', '.yml', '.json'] and 'api' in filename:
        return ArtifactSource.API_SPEC
    
    # Test files
    test_patterns = ['test', '_test', '.test', 'spec', '_spec', '.spec']
    if any(pattern in filename for pattern in test_patterns):
        return ArtifactSource.TEST
    elif 'test' in str(file_path.parent).lower():
        return ArtifactSource.TEST
    
    # Default to TEST for code files (most likely to contain behavioral assertions)
    code_extensions = ['.py', '.java', '.cs', '.js', '.ts', '.go', '.rs', '.cpp', '.c']
    if file_path.suffix.lower() in code_extensions:
        return ArtifactSource.TEST
    
    # Cannot determine type
    return None

def process_files(file_paths: List[Union[str, Path]], enable_logging: bool = True) -> ProcessResult:
    """
    Process multiple files through the complete semantic analysis pipeline.
    
    Args:
        file_paths: List of file paths to analyze
        enable_logging: Whether to enable debug logging
        
    Returns:
        ProcessResult with DisplayContext and processing statistics
    """
    
    # Initialize debug logger if enabled
    logger = ProcessLogger() if enable_logging else None
    
    try:
        # Log input files
        if logger:
            detected_types = {}
            for fp in file_paths:
                file_type = detect_file_type(fp)
                detected_types[str(fp)] = file_type.value if file_type else "UNKNOWN"
            logger.log_file_inputs(file_paths, detected_types)
    
        # Stage 1: Evidence Extraction
        all_evidence: List[Evidence] = []
        
        if logger:
            with logger.stage("Evidence Extraction", {"input_files": len(file_paths)}) as stage:
                stage.set_input_count(len(file_paths))
                
                for file_path in file_paths:
                    file_type = detect_file_type(file_path)
                    if file_type is not None:
                        stage.log_message(f"Processing {Path(file_path).name} as {file_type.value}")
                        try:
                            file_evidence = extract_evidence_from_file(str(file_path), file_type)
                            all_evidence.extend(file_evidence)
                            stage.log_message(f"Extracted {len(file_evidence)} evidence items")
                        except Exception as e:
                            stage.add_error(f"Failed to extract evidence from {file_path}: {str(e)}")
                    else:
                        stage.log_message(f"Skipping {Path(file_path).name} - unknown file type")
                
                stage.set_output_count(len(all_evidence))
                logger.log_evidence_details(all_evidence)
        else:
            for file_path in file_paths:
                file_type = detect_file_type(file_path)
                if file_type is not None:
                    file_evidence = extract_evidence_from_file(str(file_path), file_type)
                    all_evidence.extend(file_evidence)

        # Stage 2: Evidence → Claims Transformation
        if logger:
            with logger.stage("Claims Generation", {"evidence_count": len(all_evidence)}) as stage:
                stage.set_input_count(len(all_evidence))
                
                generator = DeterministicClaimGenerator()
                claims, rejections = generator.process(all_evidence)
                
                stage.set_output_count(len(claims))
                stage.add_detail("rejections_count", len(rejections) if rejections else 0)
                logger.log_claims_details(claims, rejections)
        else:
            generator = DeterministicClaimGenerator()
            claims, rejections = generator.process(all_evidence)

        # Stage 3: Claims Analysis (Pure Facts)
        if logger:
            with logger.stage("Claims Analysis", {"claims_count": len(claims)}) as stage:
                stage.set_input_count(len(claims))
                
                analyses: List[AnalysisObject] = analyse_claims(claims)
                
                stage.set_output_count(len(analyses))
                logger.log_analysis_details(analyses)
        else:
            analyses: List[AnalysisObject] = analyse_claims(claims)

        # Stage 4: Claims Evaluation (Heuristics & Scoring) 
        evaluations: List[EvaluationObject] = []
        
        if logger:
            with logger.stage("Claims Evaluation", {"analyses_count": len(analyses)}) as stage:
                stage.set_input_count(len(analyses))
                
                for analysis in analyses:
                    evaluation = evaluate_bucket(analysis.claims, analysis.findings)
                    evaluations.append(evaluation)
                
                stage.set_output_count(len(evaluations))
                logger.log_evaluation_details(evaluations)
        else:
            for analysis in analyses:
                evaluation = evaluate_bucket(analysis.claims, analysis.findings)
                evaluations.append(evaluation)

        # Stage 5: Display Context Creation (Three-Tier UI Ready)
        if logger:
            with logger.stage("Display Context Creation", {"evaluations_count": len(evaluations)}) as stage:
                stage.set_input_count(len(evaluations))
                
                display_context = create_display_context(analyses, evaluations)
                
                stage.set_output_count(1)
                logger.log_display_context_details(display_context)
        else:
            display_context = create_display_context(analyses, evaluations)

        result = ProcessResult(
            display_context=display_context,
            evidence_count=len(all_evidence),
            claims_count=len(claims),
            analysis_count=len(analyses),
            evaluation_count=len(evaluations)
        )
        
        if logger:
            logger.finalize_log(result)
        
        return result
        
    except Exception as e:
        if logger:
            logger._log_message(f"❌ FATAL ERROR: {str(e)}")
            logger.finalize_log(None)
        raise

def process_directory(directory_path: Union[str, Path], 
                     file_extensions: Optional[List[str]] = None,
                     enable_logging: bool = True) -> ProcessResult:
    """
    Process all relevant files in a directory through the semantic analysis pipeline.
    
    Args:
        directory_path: Path to directory to analyze
        file_extensions: List of file extensions to include (default: common code/doc files)
        enable_logging: Whether to enable debug logging
        
    Returns:
        ProcessResult with DisplayContext and processing statistics
    """
    
    if file_extensions is None:
        file_extensions = ['.py', '.md', '.yml', '.yaml', '.json', '.java', '.cs', '.js', '.ts']
    
    directory = Path(directory_path)
    if not directory.exists() or not directory.is_dir():
        raise ValueError(f"Directory does not exist: {directory_path}")
    
    # Find all relevant files
    file_paths = []
    for ext in file_extensions:
        file_paths.extend(directory.rglob(f'*{ext}'))
    
    return process_files(file_paths, enable_logging)

def process_single_file(file_path: Union[str, Path], enable_logging: bool = True) -> ProcessResult:
    """
    Process a single file through the semantic analysis pipeline.
    
    Args:
        file_path: Path to file to analyze
        enable_logging: Whether to enable debug logging
        
    Returns:
        ProcessResult with DisplayContext and processing statistics
    """
    
    file_path = Path(file_path)
    if not file_path.exists() or not file_path.is_file():
        raise ValueError(f"File does not exist: {file_path}")
    
    return process_files([file_path], enable_logging)

def process_codebase(codebase_path: Union[str, Path], 
                    include_tests: bool = True,
                    include_docs: bool = True,
                    custom_extensions: Optional[List[str]] = None,
                    enable_logging: bool = True) -> ProcessResult:
    """
    Process an entire codebase through the semantic analysis pipeline.
    
    This is the main entry point for codebase analysis.
    
    Args:
        codebase_path: Path to codebase root directory
        include_tests: Whether to include test files  
        include_docs: Whether to include documentation files
        custom_extensions: Custom file extensions to include
        enable_logging: Whether to enable debug logging
        
    Returns:
        ProcessResult with DisplayContext and processing statistics
    """
    
    # Build file extension list based on options
    extensions = custom_extensions or []
    
    # Core code files
    extensions.extend(['.py', '.java', '.cs', '.js', '.ts', '.go', '.rs', '.cpp', '.c', '.h'])
    
    # Configuration and API specs 
    extensions.extend(['.yml', '.yaml', '.json', '.xml'])
    
    if include_docs:
        extensions.extend(['.md', '.rst', '.txt'])
    
    if include_tests:
        # Test extensions already covered in core files
        pass
    else:
        # TODO: Could add filtering logic to exclude test directories
        pass
    
    return process_directory(codebase_path, extensions, enable_logging)

# -------------------------Main Entry Points-------------------------------------

# For single artifacts
def analyze_file(file_path: Union[str, Path]) -> DisplayContext:
    """Analyze a single file and return display context."""
    result = process_single_file(file_path, enable_logging=True)
    return result.display_context

# For multiple artifacts  
def analyze_files(file_paths: List[Union[str, Path]]) -> DisplayContext:
    """Analyze multiple files and return display context."""
    result = process_files(file_paths, enable_logging=True)
    return result.display_context

# For complete codebases - THE PRIMARY ENTRY POINT
def analyze_codebase(codebase_path: Union[str, Path], **kwargs) -> DisplayContext:
    """
    Analyze an entire codebase and return display context.
    
    This is the authoritative entry point for semantic analysis.
    Frontend should call this function.
    
    Debug logging is enabled by default. Logs are saved to backend/debug/
    """
    # Ensure logging is enabled by default for frontend calls
    if 'enable_logging' not in kwargs:
        kwargs['enable_logging'] = True
    
    result = process_codebase(codebase_path, **kwargs)
    return result.display_context

# For detailed processing information
def analyze_codebase_detailed(codebase_path: Union[str, Path], **kwargs) -> ProcessResult:
    """
    Analyze codebase and return detailed processing statistics.
    
    Use this when you need processing metrics in addition to display context.
    Debug logging is enabled by default.
    """
    # Ensure logging is enabled by default
    if 'enable_logging' not in kwargs:
        kwargs['enable_logging'] = True
        
    return process_codebase(codebase_path, **kwargs)