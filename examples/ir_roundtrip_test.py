#!/usr/bin/env python3
"""
Comprehensive IR-based round-trip test for L5X-ST conversion.
Tests the full workflow: L5X → IR → ST → IR → L5X with fidelity analysis.
"""

import sys
import os
import logging
import tempfile
from pathlib import Path

# Add the parent directory to the path to import the l5x_st_compiler module
sys.path.insert(0, str(Path(__file__).parent.parent))

from crossplc.l5x2st import L5X2STConverter
from crossplc.st2l5x import ST2L5XConverter, convert_st_to_l5x_string
from crossplc.ir_converter import IRConverter
from crossplc.models import RoundTripInfo, ConversionMetadata, ComponentMapping
import l5x

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_ir_roundtrip(l5x_file_path: str) -> RoundTripInfo:
    """Perform comprehensive IR-based round-trip test."""
    logger.info(f"Starting IR round-trip test for: {l5x_file_path}")
    
    # Step 1: L5X → IR
    logger.info("Step 1: Converting L5X to IR...")
    project = l5x.Project(l5x_file_path)
    ir_converter = IRConverter()
    original_ir = ir_converter.l5x_to_ir(project)
    
    logger.info(f"  ✓ Extracted IR with {len(original_ir.controller.tags)} tags, "
                f"{len(original_ir.controller.data_types)} data types, "
                f"{len(original_ir.controller.function_blocks)} function blocks, "
                f"{len(original_ir.programs)} programs")
    
    # Step 2: IR → ST
    logger.info("Step 2: Converting IR to ST...")
    l5x2st = L5X2STConverter()
    st_code = l5x2st.convert_l5x_to_st(l5x_file_path)
    
    logger.info(f"  ✓ Generated ST code ({len(st_code)} characters)")
    
    # Step 3: ST → IR
    logger.info("Step 3: Converting ST back to IR...")
    st2l5x = ST2L5XConverter()
    
    # Create temporary L5X from ST
    with tempfile.NamedTemporaryFile(mode='w', suffix='.L5X', delete=False) as temp_file:
        temp_l5x_path = temp_file.name
    
    try:
        # Generate L5X from ST
        l5x_xml = convert_st_to_l5x_string(st_code)
        with open(temp_l5x_path, 'w') as f:
            f.write(l5x_xml)
        
        # Parse the generated L5X and convert to IR
        generated_project = l5x.Project(temp_l5x_path)
        converted_ir = ir_converter.l5x_to_ir(generated_project)
        
        logger.info(f"  ✓ Generated IR with {len(converted_ir.controller.tags)} tags, "
                    f"{len(converted_ir.controller.data_types)} data types, "
                    f"{len(converted_ir.controller.function_blocks)} function blocks, "
                    f"{len(converted_ir.programs)} programs")
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_l5x_path):
            os.unlink(temp_l5x_path)
    
    # Step 4: IR → L5X (Final)
    logger.info("Step 4: Converting IR back to L5X...")
    final_l5x_xml = ir_converter.ir_to_l5x(converted_ir)
    
    # Save final L5X
    output_path = "ir_roundtrip_output.L5X"
    with open(output_path, 'w') as f:
        f.write(final_l5x_xml)
    
    logger.info(f"  ✓ Saved final L5X as: {output_path}")
    
    # Step 5: Calculate fidelity metrics
    logger.info("Step 5: Calculating fidelity metrics...")
    fidelity_score = ir_converter.calculate_fidelity_score(original_ir, converted_ir)
    
    # Build component mappings
    component_mappings = []
    
    # Map tags
    original_tags = {t.name: t for t in original_ir.controller.tags}
    converted_tags = {t.name: t for t in converted_ir.controller.tags}
    
    for name in original_tags:
        if name in converted_tags:
            original_tag = original_tags[name]
            converted_tag = converted_tags[name]
            mapping = ComponentMapping(
                original_name=name,
                converted_name=name,
                component_type='tag',
                conversion_notes=f"Type: {original_tag.data_type} → {converted_tag.data_type}"
            )
            component_mappings.append(mapping)
    
    # Map data types
    original_dts = {dt.name: dt for dt in original_ir.controller.data_types}
    converted_dts = {dt.name: dt for dt in converted_ir.controller.data_types}
    
    for name in original_dts:
        if name in converted_dts:
            original_dt = original_dts[name]
            converted_dt = converted_dts[name]
            mapping = ComponentMapping(
                original_name=name,
                converted_name=name,
                component_type='data_type',
                conversion_notes=f"Members: {len(original_dt.members)} → {len(converted_dt.members)}"
            )
            component_mappings.append(mapping)
    
    # Map programs
    original_progs = {p.name: p for p in original_ir.programs}
    converted_progs = {p.name: p for p in converted_ir.programs}
    
    for name in original_progs:
        if name in converted_progs:
            original_prog = original_progs[name]
            converted_prog = converted_progs[name]
            mapping = ComponentMapping(
                original_name=name,
                converted_name=name,
                component_type='program',
                conversion_notes=f"Routines: {len(original_prog.routines)} → {len(converted_prog.routines)}"
            )
            component_mappings.append(mapping)
    
    # Create metadata
    metadata = ConversionMetadata(
        source_file=l5x_file_path,
        conversion_time=ir_converter.conversion_metadata.conversion_time,
        converter_version=ir_converter.conversion_metadata.converter_version,
        original_components=ir_converter.conversion_metadata.original_components,
        converted_components={
            "tags": len(converted_ir.controller.tags),
            "data_types": len(converted_ir.controller.data_types),
            "function_blocks": len(converted_ir.controller.function_blocks),
            "programs": len(converted_ir.programs),
            "routines": sum(len(p.routines) for p in converted_ir.programs)
        }
    )
    
    # Create round-trip info
    roundtrip_info = RoundTripInfo(
        original_project=original_ir,
        converted_project=converted_ir,
        metadata=metadata,
        component_mappings=component_mappings,
        fidelity_score=fidelity_score
    )
    
    return roundtrip_info


def print_roundtrip_summary(roundtrip_info: RoundTripInfo):
    """Print comprehensive round-trip summary."""
    print("\n" + "="*80)
    print("IR ROUND-TRIP CONVERSION SUMMARY")
    print("="*80)
    
    # Basic info
    print(f"Source File: {roundtrip_info.metadata.source_file}")
    print(f"Conversion Time: {roundtrip_info.metadata.conversion_time}")
    print(f"Converter Version: {roundtrip_info.metadata.converter_version}")
    print(f"Fidelity Score: {roundtrip_info.fidelity_score:.2%}")
    
    # Component counts
    print("\nCOMPONENT COUNTS:")
    print("-" * 40)
    print("Component Type        Original    Converted    Status")
    print("-" * 40)
    
    for comp_type in ["tags", "data_types", "function_blocks", "programs", "routines"]:
        original_count = roundtrip_info.metadata.original_components.get(comp_type, 0)
        converted_count = roundtrip_info.metadata.converted_components.get(comp_type, 0)
        status = "✓" if original_count == converted_count else "⚠"
        print(f"{comp_type:20} {original_count:10} {converted_count:10} {status}")
    
    # Detailed mappings
    print("\nCOMPONENT MAPPINGS:")
    print("-" * 40)
    
    by_type = {}
    for mapping in roundtrip_info.component_mappings:
        comp_type = mapping.component_type
        if comp_type not in by_type:
            by_type[comp_type] = []
        by_type[comp_type].append(mapping)
    
    for comp_type, mappings in by_type.items():
        print(f"\n{comp_type.upper()} ({len(mappings)}):")
        for mapping in mappings[:5]:  # Show first 5
            print(f"  {mapping.original_name} → {mapping.converted_name}")
            if mapping.conversion_notes:
                print(f"    Notes: {mapping.conversion_notes}")
        if len(mappings) > 5:
            print(f"  ... and {len(mappings) - 5} more")
    
    # Warnings and errors
    if roundtrip_info.metadata.warnings:
        print(f"\nWARNINGS ({len(roundtrip_info.metadata.warnings)}):")
        print("-" * 40)
        for warning in roundtrip_info.metadata.warnings[:5]:
            print(f"  ⚠ {warning}")
        if len(roundtrip_info.metadata.warnings) > 5:
            print(f"  ... and {len(roundtrip_info.metadata.warnings) - 5} more")
    
    if roundtrip_info.metadata.errors:
        print(f"\nERRORS ({len(roundtrip_info.metadata.errors)}):")
        print("-" * 40)
        for error in roundtrip_info.metadata.errors:
            print(f"  ✗ {error}")
    
    print("\n" + "="*80)


def main():
    """Main test function."""
    if len(sys.argv) != 2:
        print("Usage: python ir_roundtrip_test.py <l5x_file>")
        print("Example: python ir_roundtrip_test.py your_project.L5X")
        sys.exit(1)
    
    l5x_file = sys.argv[1]
    
    if not os.path.exists(l5x_file):
        print(f"Error: File {l5x_file} not found")
        sys.exit(1)
    
    try:
        # Perform round-trip test
        roundtrip_info = test_ir_roundtrip(l5x_file)
        
        # Print summary
        print_roundtrip_summary(roundtrip_info)
        
        # Success message
        if roundtrip_info.fidelity_score is not None:
            if roundtrip_info.fidelity_score >= 0.8:
                print("🎉 Round-trip test PASSED with high fidelity!")
            elif roundtrip_info.fidelity_score >= 0.6:
                print("⚠️  Round-trip test PASSED with moderate fidelity")
            else:
                print("❌ Round-trip test FAILED - low fidelity detected")
        else:
            print("⚠️  Round-trip test completed but fidelity score unavailable")
        
        print(f"\nFinal L5X saved as: ir_roundtrip_output.L5X")
        
    except Exception as e:
        logger.error(f"Round-trip test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 