#!/usr/bin/env python3
"""
L5K Overlay Example

This example demonstrates how to use the L5K overlay functionality
to enhance L5X to ST conversion with additional project context.

Usage:
    python l5k_overlay_example.py
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the parent directory to the path to import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from crossplc.l5k_overlay import L5KOverlay
from crossplc.ir_converter import IRConverter
from crossplc.models import IRProject, IRController, IRTag, TagScope


def create_sample_ir_project():
    """Create a sample IR project for testing."""
    # Create a basic controller
    controller = IRController(
        name="SampleController",
        tags=[],
        data_types=[],
        function_blocks=[]
    )
    
    # Create IR project
    ir_project = IRProject(
        controller=controller,
        programs=[],
        modules=[],
        tasks=[],
        metadata={"source": "sample"}
    )
    
    return ir_project


def demonstrate_l5k_overlay():
    """Demonstrate L5K overlay functionality."""
    print("=== L5K Overlay Example ===\n")
    
    # Path to sample L5K file
    l5k_file = Path(__file__).parent / "sample_project.L5K"
    
    if not l5k_file.exists():
        print(f"❌ Sample L5K file not found: {l5k_file}")
        print("Please ensure the sample_project.L5K file exists in the examples directory.")
        return
    
    print(f"📁 Using L5K file: {l5k_file}\n")
    
    try:
        # Create L5K overlay
        print("1. Creating L5K overlay...")
        overlay = L5KOverlay(str(l5k_file))
        
        # Show summary
        summary = overlay.get_summary()
        print(f"✅ L5K overlay created successfully!")
        print(f"   - Tags: {summary['tags_count']}")
        print(f"   - Tasks: {summary['tasks_count']}")
        print(f"   - Programs: {summary['programs_count']}")
        print(f"   - Modules: {summary['modules_count']}")
        print()
        
        # Show some details
        print("2. Parsed L5K content details:")
        print("   Tags:")
        for tag in overlay.tags[:5]:  # Show first 5 tags
            print(f"     - {tag.name}: {tag.data_type}")
            if tag.description:
                print(f"       Description: {tag.description}")
            if tag.value:
                print(f"       Initial value: {tag.value}")
        
        print("\n   Tasks:")
        for task in overlay.tasks:
            print(f"     - {task.name}: {task.task_type} (Priority: {task.priority})")
            if task.interval:
                print(f"       Interval: {task.interval}")
        
        print("\n   Programs:")
        for program in overlay.programs:
            print(f"     - {program.name}")
            if program.main_routine:
                print(f"       Main routine: {program.main_routine}")
            if program.task_name:
                print(f"       Task: {program.task_name}")
        
        print("\n   Modules:")
        for module in overlay.modules:
            print(f"     - {module.name}: {module.module_type} (Slot: {module.slot})")
        
        print()
        
        # Create sample IR project
        print("3. Creating sample IR project...")
        ir_project = create_sample_ir_project()
        print(f"✅ Sample IR project created with {len(ir_project.controller.tags)} tags")
        print()
        
        # Apply L5K overlay
        print("4. Applying L5K overlay to IR project...")
        augmented_project = overlay.apply_to_ir(ir_project)
        print(f"✅ L5K overlay applied successfully!")
        print(f"   - Tags after overlay: {len(augmented_project.controller.tags)}")
        print(f"   - Tasks after overlay: {len(augmented_project.tasks)}")
        print(f"   - Programs after overlay: {len(augmented_project.programs)}")
        print(f"   - Modules after overlay: {len(augmented_project.modules)}")
        print()
        
        # Show metadata
        print("5. Overlay metadata:")
        for key, value in augmented_project.metadata.items():
            if key.startswith('l5k_'):
                print(f"   - {key}: {value}")
        print()
        
        # Demonstrate tag merging
        print("6. Tag information enhancement:")
        for tag in augmented_project.controller.tags[:3]:  # Show first 3 tags
            print(f"   - {tag.name}:")
            print(f"     Data type: {tag.data_type}")
            print(f"     Scope: {tag.scope}")
            if tag.description:
                print(f"     Description: {tag.description}")
            if tag.initial_value:
                print(f"     Initial value: {tag.initial_value}")
            if tag.external_access:
                print(f"     External access: {tag.external_access}")
            if tag.radix:
                print(f"     Radix: {tag.radix}")
            if tag.constant:
                print(f"     Constant: {tag.constant}")
            if tag.alias_for:
                print(f"     Alias for: {tag.alias_for}")
            if tag.array_dimensions:
                print(f"     Array dimensions: {tag.array_dimensions}")
            print()
        
        print("✅ L5K overlay demonstration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during L5K overlay demonstration: {e}")
        import traceback
        traceback.print_exc()


def demonstrate_cli_integration():
    """Demonstrate CLI integration with L5K overlay."""
    print("=== CLI Integration Example ===\n")
    
    l5k_file = Path(__file__).parent / "sample_project.L5K"
    
    if not l5k_file.exists():
        print(f"❌ Sample L5K file not found: {l5k_file}")
        return
    
    print("The L5K overlay can be used with the CLI as follows:")
    print()
    print("# Convert L5X to ST with L5K overlay:")
    print(f"python -m l5x_st_compiler.cli l5x2st -i project.L5X -o output.st --l5k-overlay {l5k_file}")
    print()
    print("# Convert with IR validation and L5K overlay:")
    print(f"python -m l5x_st_compiler.cli l5x2st -i project.L5X -o output.st --use-ir --l5k-overlay {l5k_file}")
    print()
    print("The L5K overlay will provide additional context such as:")
    print("- Global and controller-scoped tag declarations")
    print("- Task/program execution mapping")
    print("- Module configurations")
    print("- Default values for tags")
    print("- Program-to-task bindings")
    print()


def main():
    """Main function."""
    print("L5K Overlay Example for L5X-ST Compiler")
    print("=" * 50)
    print()
    
    # Demonstrate L5K overlay functionality
    demonstrate_l5k_overlay()
    print()
    
    # Demonstrate CLI integration
    demonstrate_cli_integration()
    
    print("For more information, see the documentation and test files.")


if __name__ == "__main__":
    main() 