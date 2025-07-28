"""
Multi-PLC Project Analysis Module

This module provides analysis capabilities for multiple L5X-based PLC projects,
detecting cross-PLC dependencies, shared tags, and potential conflicts.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass

from .ir_converter import IRConverter
from .l5k_overlay import L5KOverlay
from .models import IRProject

logger = logging.getLogger(__name__)


@dataclass
class CrossPLCDependency:
    """Represents a cross-PLC dependency."""
    tag: str
    writer: str
    readers: List[str]
    data_type: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ConflictingTag:
    """Represents a tag conflict across PLCs."""
    tag: str
    plcs: List[str]
    conflict_type: str
    details: Dict[str, Any]


class ProjectIR:
    """Multi-PLC project analysis for detecting cross-PLC dependencies and conflicts."""
    
    def __init__(self, plc_ir_map: Dict[str, IRProject]):
        """
        Initialize ProjectIR with a map of PLC names to IR projects.
        
        Args:
            plc_ir_map: Dictionary mapping PLC names to IRProject instances
        """
        self.plc_ir_map = plc_ir_map
        self.plc_names = list(plc_ir_map.keys())
        
        # Build tag usage maps for analysis
        self._build_tag_usage_maps()
    
    @classmethod
    def from_files(cls, l5x_files: List[Path], l5k_overlays: Optional[Dict[str, Path]] = None) -> "ProjectIR":
        """
        Create ProjectIR from L5X files with optional L5K overlays.
        
        Args:
            l5x_files: List of L5X file paths
            l5k_overlays: Optional dictionary mapping PLC names to L5K overlay paths
            
        Returns:
            ProjectIR instance
        """
        plc_ir_map = {}
        missing_overlays = []
        
        # Load each L5X file
        for l5x_path in l5x_files:
            plc_name = cls._extract_plc_name(l5x_path)
            
            # Check if L5K overlay is available
            l5k_path = None
            if l5k_overlays and plc_name in l5k_overlays:
                l5k_path = l5k_overlays[plc_name]
            elif l5k_overlays:
                # Try to find matching L5K file
                l5k_path = cls._find_matching_l5k(l5x_path, l5k_overlays.values())
            
            if not l5k_path:
                missing_overlays.append(plc_name)
                logger.warning(f"⚠️ L5K overlay not provided for {plc_name} — tag and task context may be incomplete.")
            
            # Convert L5X to IR
            ir_project = cls._load_plc_ir(l5x_path, l5k_path)
            plc_ir_map[plc_name] = ir_project
        
        return cls(plc_ir_map), missing_overlays
    
    @classmethod
    def _extract_plc_name(cls, l5x_path: Path) -> str:
        """Extract PLC name from L5X file path."""
        # Try to extract PLC name from filename (e.g., "P1.L5X" -> "P1")
        stem = l5x_path.stem
        if stem.startswith('P') and stem[1:].isdigit():
            return stem
        elif stem.upper().startswith('PLC'):
            return stem
        else:
            # Use filename as PLC name
            return stem
    
    @classmethod
    def _find_matching_l5k(cls, l5x_path: Path, l5k_paths: List[Path]) -> Optional[Path]:
        """Find matching L5K file for an L5X file."""
        l5x_stem = l5x_path.stem
        
        for l5k_path in l5k_paths:
            if l5k_path.stem == l5x_stem:
                return l5k_path
        
        return None
    
    @classmethod
    def _load_plc_ir(cls, l5x_path: Path, l5k_path: Optional[Path] = None) -> IRProject:
        """Load L5X file and convert to IR with optional L5K overlay."""
        import l5x
        
        # Load L5X project
        project = l5x.Project(str(l5x_path))
        
        # Apply L5K overlay if available
        if l5k_path:
            overlay = L5KOverlay(str(l5k_path))
            # Apply overlay to project (this would need to be implemented in L5KOverlay)
            # For now, we'll proceed without overlay integration
            logger.info(f"L5K overlay available for {l5x_path.name}: {l5k_path.name}")
        
        # Convert to IR
        ir_converter = IRConverter()
        ir_project = ir_converter.l5x_to_ir(project)
        
        return ir_project
    
    def _build_tag_usage_maps(self):
        """Build maps of tag usage across all PLCs."""
        self.tag_writers = {}  # tag -> {plc_name: [routines]}
        self.tag_readers = {}  # tag -> {plc_name: [routines]}
        self.tag_definitions = {}  # tag -> {plc_name: tag_definition}
        
        for plc_name, ir_project in self.plc_ir_map.items():
            # Analyze controller tags
            for tag in ir_project.controller.tags:
                tag_name = tag.name
                
                # Track tag definition
                if tag_name not in self.tag_definitions:
                    self.tag_definitions[tag_name] = {}
                self.tag_definitions[tag_name][plc_name] = {
                    "data_type": tag.data_type,
                    "scope": tag.scope.value,
                    "description": tag.description
                }
            
            # Analyze program tags and routine usage
            for program in ir_project.programs:
                for routine in program.routines:
                    if routine.content:
                        self._analyze_routine_tag_usage(plc_name, routine)
    
    def _analyze_routine_tag_usage(self, plc_name: str, routine):
        """Analyze tag usage in a routine."""
        content = routine.content
        if not content:
            return
        
        # Simple tag extraction (reusing logic from export_ir.py)
        import re
        tag_pattern = r'\b[A-Z][A-Z0-9_]*(\.[A-Z][A-Z0-9_]*)*(\[[^\]]*\])?\b'
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            
            # Look for assignments (LHS = RHS)
            if ':=' in line:
                parts = line.split(':=')
                if len(parts) == 2:
                    lhs = parts[0].strip()
                    rhs = parts[1].strip().rstrip(';')
                    
                    # LHS is a writer
                    tag = self._extract_tag_from_expression(lhs)
                    if tag:
                        if tag not in self.tag_writers:
                            self.tag_writers[tag] = {}
                        if plc_name not in self.tag_writers[tag]:
                            self.tag_writers[tag][plc_name] = []
                        self.tag_writers[tag][plc_name].append(routine.name)
                    
                    # RHS tags are readers
                    rhs_tags = self._extract_tags_from_expression(rhs)
                    for tag in rhs_tags:
                        if tag not in self.tag_readers:
                            self.tag_readers[tag] = {}
                        if plc_name not in self.tag_readers[tag]:
                            self.tag_readers[tag][plc_name] = []
                        self.tag_readers[tag][plc_name].append(routine.name)
            
            # Look for conditions in IF statements
            elif line.upper().startswith('IF '):
                condition = line[3:].strip()
                if condition.endswith('THEN'):
                    condition = condition[:-4].strip()
                
                condition_tags = self._extract_tags_from_expression(condition)
                for tag in condition_tags:
                    if tag not in self.tag_readers:
                        self.tag_readers[tag] = {}
                    if plc_name not in self.tag_readers[tag]:
                        self.tag_readers[tag][plc_name] = []
                    self.tag_readers[tag][plc_name].append(routine.name)
    
    def _extract_tag_from_expression(self, expr: str) -> Optional[str]:
        """Extract a single tag from an expression."""
        import re
        tag_pattern = r'\b[A-Z][A-Z0-9_]*(\.[A-Z][A-Z0-9_]*)*(\[[^\]]*\])?\b'
        matches = re.findall(tag_pattern, expr)
        if matches:
            return matches[0][0]
        return None
    
    def _extract_tags_from_expression(self, expr: str) -> Set[str]:
        """Extract all tags from an expression."""
        import re
        tags = set()
        tag_pattern = r'\b[A-Z][A-Z0-9_]*(\.[A-Z][A-Z0-9_]*)*(\[[^\]]*\])?\b'
        matches = re.findall(tag_pattern, expr)
        
        for match in matches:
            if match[0]:
                tag_name = match[0]
                if '[' in tag_name:
                    tag_name = tag_name.split('[')[0]
                tags.add(tag_name)
        
        return tags
    
    def find_cross_plc_dependencies(self) -> List[CrossPLCDependency]:
        """Find tags written by one PLC and read by others."""
        dependencies = []
        
        for tag in set(self.tag_writers.keys()) & set(self.tag_readers.keys()):
            writers = self.tag_writers[tag]
            readers = self.tag_readers[tag]
            
            # Find cross-PLC dependencies
            for writer_plc in writers:
                for reader_plc in readers:
                    if writer_plc != reader_plc:
                        # Get tag definition for additional info
                        tag_def = None
                        if tag in self.tag_definitions:
                            if writer_plc in self.tag_definitions[tag]:
                                tag_def = self.tag_definitions[tag][writer_plc]
                        
                        dependency = CrossPLCDependency(
                            tag=tag,
                            writer=writer_plc,
                            readers=[reader_plc],
                            data_type=tag_def.get("data_type") if tag_def else None,
                            description=tag_def.get("description") if tag_def else None
                        )
                        dependencies.append(dependency)
        
        return dependencies
    
    def detect_conflicting_tags(self) -> List[ConflictingTag]:
        """Detect tags with conflicting definitions across PLCs."""
        conflicts = []
        
        for tag in self.tag_definitions:
            if len(self.tag_definitions[tag]) > 1:
                # Check for conflicts
                definitions = self.tag_definitions[tag]
                plcs = list(definitions.keys())
                
                # Check for data type conflicts
                data_types = set(tag_def.get("data_type") for tag_def in definitions.values())
                if len(data_types) > 1:
                    conflict = ConflictingTag(
                        tag=tag,
                        plcs=plcs,
                        conflict_type="different_data_types",
                        details={
                            "data_types": {plc: tag_def.get("data_type") for plc, tag_def in definitions.items()}
                        }
                    )
                    conflicts.append(conflict)
                
                # Check for scope conflicts
                scopes = set(tag_def.get("scope") for tag_def in definitions.values())
                if len(scopes) > 1:
                    conflict = ConflictingTag(
                        tag=tag,
                        plcs=plcs,
                        conflict_type="different_scopes",
                        details={
                            "scopes": {plc: tag_def.get("scope") for plc, tag_def in definitions.items()}
                        }
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def export_summary(self, output_path: Path) -> Dict[str, Any]:
        """Export a structured JSON report of multi-PLC analysis."""
        # Find cross-PLC dependencies
        dependencies = self.find_cross_plc_dependencies()
        
        # Detect conflicts
        conflicts = self.detect_conflicting_tags()
        
        # Build shared tags summary
        shared_tags = []
        for dep in dependencies:
            shared_tags.append({
                "tag": dep.tag,
                "writer": dep.writer,
                "readers": dep.readers,
                "data_type": dep.data_type,
                "description": dep.description
            })
        
        # Build conflicting tags summary
        conflicting_tags = []
        for conflict in conflicts:
            conflicting_tags.append({
                "tag": conflict.tag,
                "plcs": conflict.plcs,
                "conflict": conflict.conflict_type,
                "details": conflict.details
            })
        
        # Build summary
        summary = {
            "metadata": {
                "total_plcs": len(self.plc_names),
                "plc_names": self.plc_names,
                "total_shared_tags": len(shared_tags),
                "total_conflicts": len(conflicting_tags)
            },
            "shared_tags": shared_tags,
            "conflicting_tags": conflicting_tags,
            "plc_summary": {}
        }
        
        # Add per-PLC summary
        for plc_name, ir_project in self.plc_ir_map.items():
            summary["plc_summary"][plc_name] = {
                "controller_tags": len(ir_project.controller.tags),
                "programs": len(ir_project.programs),
                "routines": sum(len(p.routines) for p in ir_project.programs)
            }
        
        # Write to file
        import json
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        return summary 