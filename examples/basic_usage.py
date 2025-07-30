#!/usr/bin/env python3
"""
Basic usage examples for the L5X-ST compiler.

This script demonstrates:
1. Converting a single L5X file to ST
2. Converting a directory of L5X files to consolidated ST
3. Converting ST back to L5X
4. Using the IR validation system
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from crossplc.l5x2st import L5X2STConverter
from crossplc.st2l5x import ST2L5XConverter, convert_st_to_l5x_string
from crossplc.ir_converter import IRConverter

def example_1_single_file_conversion():
    """Example 1: Convert a single L5X file to ST."""
    print("=" * 60)
    print("EXAMPLE 1: Single L5X File to ST Conversion")
    print("=" * 60)
    
    # Replace with your actual L5X file path
    input_file = "your_project.L5X"  # User should replace with actual file
    output_file = "output.st"
    
    if not os.path.exists(input_file):
        print(f"⚠️  File {input_file} not found. Skipping this example.")
        print("   To run this example, provide a valid L5X file path.")
        return
    
    try:
        converter = L5X2STConverter()
        converter.convert_file(input_file, output_file)
        
        print(f"✅ Successfully converted {input_file} to {output_file}")
        
        # Show some statistics
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                content = f.read()
                print(f"   ST file size: {len(content):,} characters")
                print(f"   Preview: {content[:200]}...")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def example_2_directory_conversion():
    """Example 2: Convert a directory of L5X files to consolidated ST."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Directory of L5X Files to Consolidated ST")
    print("=" * 60)
    
    # Replace with your actual directory path
    input_dir = "your_l5x_files"  # User should replace with actual directory
    output_file = "consolidated.st"
    
    if not os.path.exists(input_dir):
        print(f"⚠️  Directory {input_dir} not found. Skipping this example.")
        print("   To run this example, provide a valid directory path.")
        return
    
    try:
        converter = L5X2STConverter()
        converter.convert_directory(input_dir, output_file)
        
        print(f"✅ Successfully converted all L5X files in {input_dir} to {output_file}")
        
        # Show some statistics
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                content = f.read()
                print(f"   Consolidated ST file size: {len(content):,} characters")
                print(f"   Preview: {content[:200]}...")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def example_3_st_to_l5x_conversion():
    """Example 3: Convert ST back to L5X."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: ST to L5X Conversion")
    print("=" * 60)
    
    # Sample ST code
    st_code = """
VAR
    // Controller tags
    Start_Button : BOOL;
    Stop_Button : BOOL;
    Motor_Run : BOOL;
    Timer_Done : BOOL;
    Counter_Value : INT;
    
    // Program tags
    Local_Var : REAL;
    Status_Word : DINT;
END_VAR

// Program logic
IF Start_Button AND NOT Stop_Button THEN
    Motor_Run := TRUE;
    Counter_Value := Counter_Value + 1;
END_IF;

IF Stop_Button THEN
    Motor_Run := FALSE;
END_IF;

Local_Var := Local_Var * 2.5;
Status_Word := 16#1234;
"""
    
    try:
        # Convert ST to L5X
        l5x_xml = convert_st_to_l5x_string(st_code)
        
        # Write to file
        output_file = "generated_project.L5X"
        with open(output_file, 'w') as f:
            f.write(l5x_xml)
        
        print(f"✅ Successfully converted ST code to {output_file}")
        print(f"   L5X file size: {len(l5x_xml):,} characters")
        print(f"   Preview: {l5x_xml[:200]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def example_4_ir_validation():
    """Example 4: Using IR validation for round-trip conversion."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: IR Validation and Round-Trip Conversion")
    print("=" * 60)
    
    # Replace with your actual L5X file path
    input_file = "your_project.L5X"  # User should replace with actual file
    
    if not os.path.exists(input_file):
        print(f"⚠️  File {input_file} not found. Skipping this example.")
        print("   To run this example, provide a valid L5X file path.")
        return
    
    try:
        # Initialize converters
        l5x2st = L5X2STConverter()
        ir_converter = IRConverter()
        
        # Load original L5X and convert to IR
        import l5x
        original_project = l5x.Project(input_file)
        original_ir = ir_converter.l5x_to_ir(original_project)
        
        print(f"✅ Loaded original project: {input_file}")
        print(f"   Controller tags: {len(original_ir.controller.tags)}")
        print(f"   Programs: {len(original_ir.programs)}")
        
        # Convert to ST
        st_output = "ir_test.st"
        l5x2st.convert_file(input_file, st_output)
        
        # Read ST and convert back to L5X
        with open(st_output, 'r') as f:
            st_content = f.read()
        
        final_l5x = "ir_test_output.L5X"
        l5x_xml = convert_st_to_l5x_string(st_content)
        with open(final_l5x, 'w') as f:
            f.write(l5x_xml)
        
        # Load final L5X and convert to IR
        final_project = l5x.Project(final_l5x)
        final_ir = ir_converter.l5x_to_ir(final_project)
        
        # Calculate fidelity score
        fidelity_score = ir_converter.calculate_fidelity_score(original_ir, final_ir)
        
        print(f"✅ Round-trip conversion completed!")
        print(f"   Fidelity score: {fidelity_score:.2%}")
        print(f"   Original tags: {len(original_ir.controller.tags)}")
        print(f"   Final tags: {len(final_ir.controller.tags)}")
        
        # Clean up
        for temp_file in [st_output, final_l5x]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run all examples."""
    print("L5X-ST Compiler - Basic Usage Examples")
    print("=" * 60)
    
    # Run examples
    example_1_single_file_conversion()
    example_2_directory_conversion()
    example_3_st_to_l5x_conversion()
    example_4_ir_validation()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
    print("\nNote: Some examples require actual L5X files to run.")
    print("Replace the placeholder paths with your actual file paths.")

if __name__ == "__main__":
    main() 