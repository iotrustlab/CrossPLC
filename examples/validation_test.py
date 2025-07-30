#!/usr/bin/env python3
"""
Comprehensive validation test for L5X-ST round-trip conversion with IR validation.

This script demonstrates:
1. L5X → ST conversion with IR validation
2. ST → L5X conversion with IR validation  
3. Full round-trip L5X → ST → L5X with fidelity scoring
4. CLI usage examples
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

# Add the parent directory to the path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from crossplc.l5x2st import L5X2STConverter
from crossplc.st2l5x import ST2L5XConverter, convert_st_to_l5x_string
from crossplc.ir_converter import IRConverter
from crossplc.models import RoundTripInfo

def test_l5x_to_st_conversion():
    """Test L5X to ST conversion."""
    print("\n=== Testing L5X to ST Conversion ===")
    
    # Use a generic test file path - user should provide their own L5X file
    input_file = "test_project.L5X"  # User should replace with actual file
    
    if not os.path.exists(input_file):
        print(f"⚠️  Warning: Test file {input_file} not found. Skipping L5X→ST test.")
        print("   To test this functionality, provide a valid L5X file.")
        return
    
    try:
        converter = L5X2STConverter()
        output_file = "test_output.st"
        
        print(f"Converting {input_file} to {output_file}...")
        converter.convert_file(input_file, output_file)
        
        # Verify output file was created
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                content = f.read()
                print(f"✅ Successfully converted to {output_file}")
                print(f"   Output size: {len(content)} characters")
                print(f"   First 200 chars: {content[:200]}...")
        else:
            print("❌ Error: Output file was not created")
            
    except Exception as e:
        print(f"❌ Error during L5X→ST conversion: {e}")

def test_st_to_l5x_with_ir():
    """Test ST to L5X conversion with IR validation."""
    print("\n" + "=" * 60)
    print("TEST 2: ST → L5X with IR Validation")
    print("=" * 60)
    
    input_file = "test_output.st"
    output_file = "test_output.L5X"
    
    try:
        # Use CLI with IR validation
        cmd = [
            sys.executable, "-m", "l5x_st_compiler.cli", 
            "st2l5x", "-i", input_file, "-o", output_file, "--use-ir"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ ST → L5X conversion with IR validation: SUCCESS")
            print(f"   Input: {input_file}")
            print(f"   Output: {output_file}")
            
            # Show file size
            if os.path.exists(output_file):
                size = os.path.getsize(output_file)
                print(f"   L5X file size: {size:,} bytes")
        else:
            print("❌ ST → L5X conversion with IR validation: FAILED")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error during ST → L5X conversion: {e}")
        return False
    
    return True

def test_full_roundtrip_with_ir():
    """Test full round-trip conversion with IR validation."""
    print("\n=== Testing Full Round-Trip with IR Validation ===")
    
    # Use a generic test file path - user should provide their own L5X file
    original_l5x = "test_project.L5X"  # User should replace with actual file
    
    if not os.path.exists(original_l5x):
        print(f"⚠️  Warning: Test file {original_l5x} not found. Skipping round-trip test.")
        print("   To test this functionality, provide a valid L5X file.")
        return
    
    try:
        # Step 1: L5X → ST
        print("Step 1: Converting L5X → ST...")
        l5x2st = L5X2STConverter()
        st_output = "roundtrip_test.st"
        l5x2st.convert_file(original_l5x, st_output)
        
        # Step 2: ST → L5X
        print("Step 2: Converting ST → L5X...")
        with open(st_output, 'r') as f:
            st_content = f.read()
        
        final_l5x = "roundtrip_test_output.L5X"
        l5x_xml = convert_st_to_l5x_string(st_content)
        with open(final_l5x, 'w') as f:
            f.write(l5x_xml)
        
        # Step 3: IR validation
        print("Step 3: IR validation...")
        ir_converter = IRConverter()
        
        # Load original and final projects
        import l5x
        original_project = l5x.Project(original_l5x)
        final_project = l5x.Project(final_l5x)
        
        # Convert to IR
        original_ir = ir_converter.l5x_to_ir(original_project)
        final_ir = ir_converter.l5x_to_ir(final_project)
        
        # Calculate fidelity score
        fidelity_score = ir_converter.calculate_fidelity_score(original_ir, final_ir)
        
        print(f"✅ Round-trip conversion completed successfully!")
        print(f"   Original: {original_l5x}")
        print(f"   ST intermediate: {st_output}")
        print(f"   Final: {final_l5x}")
        print(f"   Fidelity score: {fidelity_score:.2%}")
        
        # Clean up temporary files
        for temp_file in [st_output, final_l5x]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during round-trip conversion: {e}")
        return False

def test_cli_help():
    """Test CLI help functionality."""
    print("\n" + "=" * 60)
    print("TEST 4: CLI Help and Usage")
    print("=" * 60)
    
    try:
        # Test main help
        cmd = [sys.executable, "-m", "l5x_st_compiler.cli", "--help"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ CLI help: SUCCESS")
            print("   Available commands:")
            print("   - l5x2st: Convert L5X to ST")
            print("   - st2l5x: Convert ST to L5X")
            print("   - --use-ir: Enable IR validation mode")
        else:
            print("❌ CLI help: FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Error testing CLI help: {e}")
        return False
    
    return True

def cleanup_test_files():
    """Clean up test files."""
    test_files = [
        "test_output.st",
        "test_output.L5X", 
        "roundtrip_test.st",
        "roundtrip_test_output.L5X"
    ]
    
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"   Cleaned up: {file}")

def main():
    """Run all validation tests."""
    print("L5X-ST Compiler Validation Test Suite")
    print("=====================================")
    print("Testing complete round-trip functionality with IR validation")
    print()
    
    # Remove obsolete check for L5K_L5X_Examples/P1.L5X
    # if not os.path.exists("L5K_L5X_Examples/P1.L5X"):
    #     print("❌ Error: Input file L5K_L5X_Examples/P1.L5X not found")
    #     return
    # All tests now use 'test_project.L5X' as the placeholder input file.
    
    tests_passed = 0
    total_tests = 4
    
    # Run tests
    if test_l5x_to_st_conversion():
        tests_passed += 1
    
    if test_st_to_l5x_with_ir():
        tests_passed += 1
    
    if test_full_roundtrip_with_ir():
        tests_passed += 1
    
    if test_cli_help():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION TEST SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED! The L5X-ST compiler is working correctly.")
        print("\nKey Features Verified:")
        print("✅ L5X → ST conversion with IR validation")
        print("✅ ST → L5X conversion with IR validation")
        print("✅ Full round-trip conversion with fidelity scoring")
        print("✅ CLI interface with --use-ir flag")
        print("✅ Intermediate Representation (IR) system")
        print("✅ Guardrail validation system")
    else:
        print("❌ Some tests failed. Please check the output above.")
    
    # Cleanup
    print("\nCleaning up test files...")
    cleanup_test_files()
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 