#!/usr/bin/env python3
"""
Validate L5K Overlay Difference - IR Comparison

This script compares the Intermediate Representation (IR) before and after applying 
the L5K overlay to quantify how much project metadata (tags, tasks, modules, etc.) 
is added by the L5K file.

Usage:
    python validate_l5k_overlay_diff.py [--compare-ir] [--output-file] [--project P1]

Examples:
    python validate_l5k_overlay_diff.py --project P1
    python validate_l5k_overlay_diff.py --compare-ir --output-file ir_comparison.json
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Add the parent directory to the path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

import l5x
from l5x_st_compiler.ir_converter import IRConverter
from l5x_st_compiler.models import IRProject


def summarize_ir(ir_project: IRProject) -> Dict[str, Any]:
    """
    Summarize an IR project and return counts of various components.
    
    Args:
        ir_project: The IR project to summarize
        
    Returns:
        Dictionary with component counts
    """
    summary = {
        'controller_name': ir_project.controller.name,
        'tags': {
            'total': len(ir_project.controller.tags),
            'controller_scope': len([t for t in ir_project.controller.tags if t.scope.value == 'Controller']),
            'program_scope': len([t for t in ir_project.controller.tags if t.scope.value == 'Program']),
            'with_initial_values': len([t for t in ir_project.controller.tags if t.initial_value]),
            'with_descriptions': len([t for t in ir_project.controller.tags if t.description]),
            'constants': len([t for t in ir_project.controller.tags if t.constant]),
            'aliases': len([t for t in ir_project.controller.tags if t.alias_for]),
        },
        'data_types': {
            'total': len(ir_project.controller.data_types),
            'with_members': len([dt for dt in ir_project.controller.data_types if dt.members]),
            'enums': len([dt for dt in ir_project.controller.data_types if dt.is_enum]),
        },
        'function_blocks': {
            'total': len(ir_project.controller.function_blocks),
            'with_parameters': len([fb for fb in ir_project.controller.function_blocks if fb.parameters]),
            'with_implementation': len([fb for fb in ir_project.controller.function_blocks if fb.implementation]),
        },
        'programs': {
            'total': len(ir_project.programs),
            'with_routines': len([p for p in ir_project.programs if p.routines]),
            'with_main_routine': len([p for p in ir_project.programs if p.main_routine]),
            'with_descriptions': len([p for p in ir_project.programs if p.description]),
        },
        'tasks': {
            'total': len(ir_project.tasks),
            'continuous': len([t for t in ir_project.tasks if t.get('type') == 'CONTINUOUS']),
            'periodic': len([t for t in ir_project.tasks if t.get('type') == 'PERIODIC']),
            'event': len([t for t in ir_project.tasks if t.get('type') == 'EVENT']),
        },
        'modules': {
            'total': len(ir_project.modules),
            'with_configuration': len([m for m in ir_project.modules if m.get('configuration')]),
        },
        'metadata': ir_project.metadata.copy(),
    }
    
    # Count program-task mappings (from metadata)
    program_task_mappings = 0
    if 'program_task_mappings' in ir_project.metadata:
        program_task_mappings = ir_project.metadata['program_task_mappings']
    
    summary['program_task_mappings'] = program_task_mappings
    
    return summary


def compare_ir_summaries(before_summary: Dict[str, Any], after_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare two IR summaries and calculate deltas.
    
    Args:
        before_summary: Summary before L5K overlay
        after_summary: Summary after L5K overlay
        
    Returns:
        Dictionary with comparison results
    """
    comparison = {
        'controller_name': {
            'before': before_summary['controller_name'],
            'after': after_summary['controller_name'],
        },
        'tags': {},
        'data_types': {},
        'function_blocks': {},
        'programs': {},
        'tasks': {},
        'modules': {},
        'program_task_mappings': {},
        'l5k_overlay_applied': after_summary['metadata'].get('l5k_overlay_applied', False),
        'l5k_source_file': after_summary['metadata'].get('l5k_source_file', None),
    }
    
    # Compare tags
    for key in before_summary['tags']:
        before_val = before_summary['tags'][key]
        after_val = after_summary['tags'][key]
        delta = after_val - before_val
        comparison['tags'][key] = {
            'before': before_val,
            'after': after_val,
            'delta': delta,
            'change': f"{before_val} → {after_val} ({delta:+d})"
        }
    
    # Compare data types
    for key in before_summary['data_types']:
        before_val = before_summary['data_types'][key]
        after_val = after_summary['data_types'][key]
        delta = after_val - before_val
        comparison['data_types'][key] = {
            'before': before_val,
            'after': after_val,
            'delta': delta,
            'change': f"{before_val} → {after_val} ({delta:+d})"
        }
    
    # Compare function blocks
    for key in before_summary['function_blocks']:
        before_val = before_summary['function_blocks'][key]
        after_val = after_summary['function_blocks'][key]
        delta = after_val - before_val
        comparison['function_blocks'][key] = {
            'before': before_val,
            'after': after_val,
            'delta': delta,
            'change': f"{before_val} → {after_val} ({delta:+d})"
        }
    
    # Compare programs
    for key in before_summary['programs']:
        before_val = before_summary['programs'][key]
        after_val = after_summary['programs'][key]
        delta = after_val - before_val
        comparison['programs'][key] = {
            'before': before_val,
            'after': after_val,
            'delta': delta,
            'change': f"{before_val} → {after_val} ({delta:+d})"
        }
    
    # Compare tasks
    for key in before_summary['tasks']:
        before_val = before_summary['tasks'][key]
        after_val = after_summary['tasks'][key]
        delta = after_val - before_val
        comparison['tasks'][key] = {
            'before': before_val,
            'after': after_val,
            'delta': delta,
            'change': f"{before_val} → {after_val} ({delta:+d})"
        }
    
    # Compare modules
    for key in before_summary['modules']:
        before_val = before_summary['modules'][key]
        after_val = after_summary['modules'][key]
        delta = after_val - before_val
        comparison['modules'][key] = {
            'before': before_val,
            'after': after_val,
            'delta': delta,
            'change': f"{before_val} → {after_val} ({delta:+d})"
        }
    
    # Compare program-task mappings
    before_mappings = before_summary.get('program_task_mappings', 0)
    after_mappings = after_summary.get('program_task_mappings', 0)
    delta_mappings = after_mappings - before_mappings
    comparison['program_task_mappings'] = {
        'before': before_mappings,
        'after': after_mappings,
        'delta': delta_mappings,
        'change': f"{before_mappings} → {after_mappings} ({delta_mappings:+d})"
    }
    
    return comparison


def print_comparison_report(comparison: Dict[str, Any], project_name: str):
    """
    Print a human-readable comparison report.
    
    Args:
        comparison: Comparison results
        project_name: Name of the project being compared
    """
    print(f"\n{'='*80}")
    print(f"L5K OVERLAY COMPARISON REPORT: {project_name}")
    print(f"{'='*80}")
    
    # L5K overlay status
    if comparison['l5k_overlay_applied']:
        print(f"✅ L5K Overlay Applied: {comparison['l5k_source_file']}")
    else:
        print("❌ L5K Overlay Not Applied")
    
    print(f"\nController: {comparison['controller_name']['before']} → {comparison['controller_name']['after']}")
    
    # Tags comparison
    print(f"\n📊 TAGS:")
    print(f"   Total Tags: {comparison['tags']['total']['change']}")
    print(f"   Controller Scope: {comparison['tags']['controller_scope']['change']}")
    print(f"   Program Scope: {comparison['tags']['program_scope']['change']}")
    print(f"   With Initial Values: {comparison['tags']['with_initial_values']['change']}")
    print(f"   With Descriptions: {comparison['tags']['with_descriptions']['change']}")
    print(f"   Constants: {comparison['tags']['constants']['change']}")
    print(f"   Aliases: {comparison['tags']['aliases']['change']}")
    
    # Data Types comparison
    print(f"\n📋 DATA TYPES:")
    print(f"   Total UDTs: {comparison['data_types']['total']['change']}")
    print(f"   With Members: {comparison['data_types']['with_members']['change']}")
    print(f"   Enums: {comparison['data_types']['enums']['change']}")
    
    # Function Blocks comparison
    print(f"\n🔧 FUNCTION BLOCKS:")
    print(f"   Total FBs: {comparison['function_blocks']['total']['change']}")
    print(f"   With Parameters: {comparison['function_blocks']['with_parameters']['change']}")
    print(f"   With Implementation: {comparison['function_blocks']['with_implementation']['change']}")
    
    # Programs comparison
    print(f"\n📝 PROGRAMS:")
    print(f"   Total Programs: {comparison['programs']['total']['change']}")
    print(f"   With Routines: {comparison['programs']['with_routines']['change']}")
    print(f"   With Main Routine: {comparison['programs']['with_main_routine']['change']}")
    print(f"   With Descriptions: {comparison['programs']['with_descriptions']['change']}")
    
    # Tasks comparison
    print(f"\n⏱️  TASKS:")
    print(f"   Total Tasks: {comparison['tasks']['total']['change']}")
    print(f"   Continuous: {comparison['tasks']['continuous']['change']}")
    print(f"   Periodic: {comparison['tasks']['periodic']['change']}")
    print(f"   Event: {comparison['tasks']['event']['change']}")
    
    # Modules comparison
    print(f"\n🔌 MODULES:")
    print(f"   Total Modules: {comparison['modules']['total']['change']}")
    print(f"   With Configuration: {comparison['modules']['with_configuration']['change']}")
    
    # Program-Task mappings
    print(f"\n🔗 PROGRAM-TASK MAPPINGS:")
    print(f"   Total Mappings: {comparison['program_task_mappings']['change']}")
    
    # Summary
    total_additions = (
        comparison['tags']['total']['delta'] +
        comparison['data_types']['total']['delta'] +
        comparison['function_blocks']['total']['delta'] +
        comparison['tasks']['total']['delta'] +
        comparison['modules']['total']['delta'] +
        comparison['program_task_mappings']['delta']
    )
    
    print(f"\n{'='*80}")
    print(f"SUMMARY: L5K Overlay added {total_additions} total components")
    print(f"{'='*80}")


def validate_l5k_overlay_diff(project_name: str = "P1", output_file: Optional[str] = None):
    """
    Validate the difference between IR with and without L5K overlay.
    
    Args:
        project_name: Name of the project to analyze (default: P1)
        output_file: Optional file to save comparison results
    """
    # Define file paths
    l5x_file = f"../sampledata/swatfiles/{project_name}.L5X"
    l5k_file = f"../sampledata/swatfiles/{project_name}.L5K"
    
    # Check if files exist
    if not os.path.exists(l5x_file):
        print(f"❌ Error: L5X file not found: {l5x_file}")
        return False
    
    if not os.path.exists(l5k_file):
        print(f"❌ Error: L5K file not found: {l5k_file}")
        return False
    
    print(f"🔍 Analyzing {project_name} with L5K overlay...")
    print(f"   L5X: {l5x_file}")
    print(f"   L5K: {l5k_file}")
    
    try:
        # Initialize IR converter
        ir_converter = IRConverter()
        
        # Load L5X project
        project = l5x.Project(l5x_file)
        
        # Convert to IR without overlay
        print("\n📥 Converting L5X to IR (without overlay)...")
        ir_without_overlay = ir_converter.l5x_to_ir(project)
        summary_without = summarize_ir(ir_without_overlay)
        
        # Convert to IR with overlay
        print("📥 Converting L5X to IR (with L5K overlay)...")
        ir_with_overlay = ir_converter.l5x_to_ir(project, l5k_file)
        summary_with = summarize_ir(ir_with_overlay)
        
        # Compare summaries
        print("🔍 Comparing IR summaries...")
        comparison = compare_ir_summaries(summary_without, summary_with)
        
        # Print report
        print_comparison_report(comparison, project_name)
        
        # Save to file if requested
        if output_file:
            print(f"\n💾 Saving comparison to: {output_file}")
            with open(output_file, 'w') as f:
                json.dump(comparison, f, indent=2)
            print(f"✅ Comparison saved to {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during IR comparison: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate L5K overlay difference by comparing IR representations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_l5k_overlay_diff.py --project P1
  python validate_l5k_overlay_diff.py --project P2 --output-file comparison.json
  python validate_l5k_overlay_diff.py --compare-ir --project P1
        """
    )
    
    parser.add_argument(
        '--project', '-p',
        default='P1',
        help='Project name to analyze (default: P1)'
    )
    
    parser.add_argument(
        '--output-file', '-o',
        help='Output file to save comparison results (JSON format)'
    )
    
    parser.add_argument(
        '--compare-ir',
        action='store_true',
        help='Enable IR comparison mode (default behavior)'
    )
    
    args = parser.parse_args()
    
    # Run the validation
    success = validate_l5k_overlay_diff(
        project_name=args.project,
        output_file=args.output_file
    )
    
    if success:
        print("\n✅ IR comparison completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ IR comparison failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 