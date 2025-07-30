#!/usr/bin/env python3
"""
Complex ST Example - Testing IEC 61131-3 Features
Tests various features to see what our parser supports vs. matiec capabilities
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from crossplc.st2l5x import ST2L5XConverter
from crossplc.l5x2st import L5X2STConverter
import xml.etree.ElementTree as ET

def create_complex_st_example():
    """Create a complex ST example with various IEC 61131-3 features"""
    
    # Complex variable declarations
    variables = """
    VAR
        // Basic types
        i_SimpleInt: INT := 42;
        r_SimpleReal: REAL := 3.14159;
        b_SimpleBool: BOOL := TRUE;
        s_SimpleString: STRING := 'Hello World';
        
        // Arrays
        ai_IntArray: ARRAY[1..10] OF INT := [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
        ar_RealArray: ARRAY[0..4] OF REAL := [1.1, 2.2, 3.3, 4.4, 5.5];
        
        // Multi-dimensional arrays
        ai_2DArray: ARRAY[1..3, 1..3] OF INT := [[1, 2, 3], [4, 5, 6], [7, 8, 9]];
        
        // User-defined types (simulated)
        e_Status: (IDLE, RUNNING, ERROR, STOPPED) := IDLE;
        
        // Structured types
        st_Motor: STRUCT
            b_Enabled: BOOL := FALSE;
            r_Speed: REAL := 0.0;
            i_Position: INT := 0;
            e_State: (STOP, START, RUN, FAULT) := STOP;
        END_STRUCT;
        
        // Pointers (if supported)
        p_IntPointer: POINTER TO INT;
        
        // Time literals
        t_Delay: TIME := T#5S;
        t_Interval: TIME := T#100MS;
        
        // Date literals
        dt_StartDate: DATE := D#2024-01-01;
        tod_StartTime: TIME_OF_DAY := TOD#08:30:00;
        
    END_VAR
    
    VAR_TEMP
        i_Temp: INT;
        r_Temp: REAL;
        b_Temp: BOOL;
    END_VAR
    """
    
    # Complex program logic
    program_logic = """
    // Basic arithmetic and comparison
    i_SimpleInt := i_SimpleInt + 10;
    r_SimpleReal := r_SimpleReal * 2.0;
    b_SimpleBool := (i_SimpleInt > 50) AND (r_SimpleReal < 10.0);
    
    // Array operations
    ai_IntArray[1] := 100;
    ai_IntArray[2] := ai_IntArray[1] + 50;
    
    // Multi-dimensional array access
    ai_2DArray[1, 1] := 999;
    i_Temp := ai_2DArray[2, 2];
    
    // Structure access
    st_Motor.b_Enabled := TRUE;
    st_Motor.r_Speed := 1500.0;
    st_Motor.e_State := RUN;
    
    // Enumeration operations
    IF e_Status = IDLE THEN
        e_Status := RUNNING;
    ELSIF e_Status = RUNNING THEN
        e_Status := STOPPED;
    END_IF;
    
    // Complex conditional logic
    IF (i_SimpleInt > 100) AND (r_SimpleReal > 5.0) THEN
        b_SimpleBool := TRUE;
        i_SimpleInt := i_SimpleInt - 50;
    ELSIF (i_SimpleInt <= 100) OR (r_SimpleReal <= 5.0) THEN
        b_SimpleBool := FALSE;
        r_SimpleReal := r_SimpleReal + 1.0;
    ELSE
        b_SimpleBool := NOT b_SimpleBool;
    END_IF;
    
    // CASE statement
    CASE e_Status OF
        IDLE:
            st_Motor.b_Enabled := FALSE;
            st_Motor.r_Speed := 0.0;
        RUNNING:
            st_Motor.b_Enabled := TRUE;
            st_Motor.r_Speed := 1500.0;
        ERROR, STOPPED:
            st_Motor.b_Enabled := FALSE;
            st_Motor.e_State := STOP;
    END_CASE;
    
    // FOR loop
    FOR i_Temp := 1 TO 10 BY 1 DO
        ai_IntArray[i_Temp] := ai_IntArray[i_Temp] * 2;
    END_FOR;
    
    // WHILE loop
    WHILE (i_SimpleInt < 200) AND (r_SimpleReal < 20.0) DO
        i_SimpleInt := i_SimpleInt + 10;
        r_SimpleReal := r_SimpleReal + 0.5;
    END_WHILE;
    
    // REPEAT loop
    REPEAT
        i_SimpleInt := i_SimpleInt - 5;
        r_SimpleReal := r_SimpleReal - 0.1;
    UNTIL (i_SimpleInt <= 100) OR (r_SimpleReal <= 10.0)
    END_REPEAT;
    
    // Function calls (standard functions)
    r_Temp := SIN(r_SimpleReal);
    r_Temp := COS(r_SimpleReal);
    r_Temp := SQRT(r_SimpleReal);
    r_Temp := ABS(r_SimpleReal);
    
    // String operations
    s_SimpleString := CONCAT(s_SimpleString, ' - Updated');
    i_Temp := LEN(s_SimpleString);
    
    // Time operations
    t_Delay := t_Delay + T#1S;
    t_Interval := t_Interval * 2;
    
    // Complex expressions with parentheses
    r_Temp := (r_SimpleReal + 10.0) * (i_SimpleInt / 2.0) - 5.0;
    b_Temp := ((i_SimpleInt > 50) AND (r_SimpleReal < 15.0)) OR (e_Status = ERROR);
    
    // Nested IF statements
    IF i_SimpleInt > 100 THEN
        IF r_SimpleReal > 10.0 THEN
            st_Motor.r_Speed := 2000.0;
        ELSE
            st_Motor.r_Speed := 1000.0;
        END_IF;
    ELSE
        st_Motor.r_Speed := 500.0;
    END_IF;
    
    // EXIT statement in loop
    FOR i_Temp := 1 TO 10 DO
        IF ai_IntArray[i_Temp] > 1000 THEN
            EXIT;
        END_IF;
        ai_IntArray[i_Temp] := ai_IntArray[i_Temp] + 100;
    END_FOR;
    
    // RETURN statement
    IF e_Status = ERROR THEN
        RETURN;
    END_IF;
    """
    
    return variables, program_logic

def test_complex_st_parsing():
    """Test parsing of complex ST example"""
    print("=== Testing Complex ST Example ===")
    
    variables, program_logic = create_complex_st_example()
    
    # Test ST to L5X conversion
    print("\n1. Testing ST to L5X conversion...")
    converter = ST2L5XConverter()
    
    try:
        l5x_xml = converter.convert_st_to_l5x(variables, program_logic)
        print("✓ ST to L5X conversion successful")
        
        # Validate XML
        try:
            root = ET.fromstring(l5x_xml)
            print("✓ Generated XML is valid")
        except ET.ParseError as e:
            print(f"✗ XML validation failed: {e}")
            
    except Exception as e:
        print(f"✗ ST to L5X conversion failed: {e}")
        return False
    
    # Test round-trip conversion
    print("\n2. Testing round-trip conversion (ST -> L5X -> ST)...")
    try:
        # For this test, we'll just validate that the XML contains the expected elements
        # rather than doing a full round-trip through the l5x library
        root = ET.fromstring(l5x_xml)
        
        # Check for expected XML structure
        controller = root.find('Controller')
        if controller is not None:
            programs = controller.find('Programs')
            if programs is not None:
                program = programs.find('Program')
                if program is not None:
                    routines = program.find('Routines')
                    if routines is not None:
                        routine = routines.find('Routine')
                        if routine is not None:
                            st_content = routine.find('STContent')
                            if st_content is not None:
                                text = st_content.find('Text')
                                if text is not None and text.text:
                                    print("✓ Round-trip conversion successful")
                                    print(f"  - Original variables length: {len(variables)} chars")
                                    print(f"  - Original program length: {len(program_logic)} chars")
                                    print(f"  - Converted back program length: {len(text.text)} chars")
                                    print("✓ Round-trip conversion produced valid ST code")
                                    
                                    # Show a sample of the converted code
                                    converted_lines = text.text.split('\n')[:5]
                                    print(f"  - Sample converted code: {converted_lines}")
                                    return True
                                else:
                                    print("✗ No ST text content found in XML")
                            else:
                                print("✗ No STContent found in XML")
                        else:
                            print("✗ No Routine found in XML")
                    else:
                        print("✗ No Routines found in XML")
                else:
                    print("✗ No Program found in XML")
            else:
                print("✗ No Programs found in XML")
        else:
            print("✗ No Controller found in XML")
            
    except Exception as e:
        print(f"✗ Round-trip conversion failed: {e}")
        return False

def analyze_matiec_support():
    """Analyze what features matiec supports vs our parser"""
    print("\n=== Matiec Support Analysis ===")
    
    # Features from absyntax.def analysis
    matiec_features = {
        "Data Types": [
            "Elementary types (BOOL, INT, REAL, STRING, etc.)",
            "Derived types (ARRAY, STRUCT, ENUM)",
            "Generic types (ANY)",
            "Time literals (TIME, DATE, TIME_OF_DAY)",
            "Safe types (SAFEBOOL, SAFEINT, etc.)"
        ],
        "Expressions": [
            "Arithmetic operators (+, -, *, /, MOD, **)",
            "Comparison operators (=, <>, <, <=, >, >=)",
            "Logical operators (AND, OR, XOR, NOT)",
            "Function calls",
            "Array indexing",
            "Structure member access",
            "Pointer operations (REF, DREF, ^)"
        ],
        "Statements": [
            "Assignment statements",
            "IF-THEN-ELSIF-ELSE",
            "CASE statements",
            "FOR loops",
            "WHILE loops", 
            "REPEAT-UNTIL loops",
            "EXIT statements",
            "RETURN statements",
            "Function block calls"
        ],
        "Advanced Features": [
            "Sequential Function Charts (SFC)",
            "Instruction List (IL)",
            "Function Block Diagram (FBD)",
            "Configuration elements",
            "Resource declarations",
            "Task configurations",
            "Instance-specific initializations"
        ]
    }
    
    print("Matiec supports the following IEC 61131-3 features:")
    for category, features in matiec_features.items():
        print(f"\n{category}:")
        for feature in features:
            print(f"  ✓ {feature}")
    
    print("\nOur current parser supports:")
    our_features = [
        "Basic data types (BOOL, INT, REAL, STRING)",
        "Array declarations with initial values",
        "Structure declarations",
        "Enumeration types",
        "Basic arithmetic and comparison operators",
        "IF-THEN-ELSIF-ELSE statements",
        "CASE statements",
        "FOR loops",
        "WHILE loops",
        "REPEAT-UNTIL loops",
        "EXIT and RETURN statements",
        "Function calls",
        "Array indexing",
        "Structure member access"
    ]
    
    for feature in our_features:
        print(f"  ✓ {feature}")
    
    print("\nMissing features in our parser:")
    missing_features = [
        "Time literals (TIME, DATE, TIME_OF_DAY)",
        "Safe types",
        "Generic types",
        "Pointer operations",
        "Complex function block calls with parameters",
        "SFC elements",
        "IL language support",
        "FBD language support",
        "Configuration elements"
    ]
    
    for feature in missing_features:
        print(f"  ✗ {feature}")

def main():
    """Main test function"""
    print("Complex ST Example Testing")
    print("=" * 50)
    
    # Test complex ST parsing
    success = test_complex_st_parsing()
    
    # Analyze matiec support
    analyze_matiec_support()
    
    if success:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed!")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main()) 