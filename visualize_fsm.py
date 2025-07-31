#!/usr/bin/env python3
"""
FSM visualization script.
"""

import sys
import json
from pathlib import Path

def visualize_fsm_from_json(json_file: str, output_file: str):
    """Visualize FSM from JSON output."""
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    if 'fsm' not in data:
        print("❌ No FSM data found in JSON file")
        return
    
    fsm = data['fsm']
    
    # Generate DOT format
    dot_content = generate_dot_from_fsm(fsm)
    
    # Write DOT file
    dot_file = output_file.replace('.svg', '.dot')
    with open(dot_file, 'w') as f:
        f.write(dot_content)
    
    print(f"✅ DOT file written to: {dot_file}")
    
    # Try to generate SVG if graphviz is available
    try:
        import subprocess
        result = subprocess.run(['dot', '-Tsvg', dot_file, '-o', output_file], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ SVG file written to: {output_file}")
        else:
            print(f"⚠️ Could not generate SVG: {result.stderr}")
            print("You can manually run: dot -Tsvg {dot_file} -o {output_file}")
    except FileNotFoundError:
        print("⚠️ Graphviz not found. Install with: brew install graphviz")
        print(f"You can manually run: dot -Tsvg {dot_file} -o {output_file}")

def generate_dot_from_fsm(fsm: dict) -> str:
    """Generate DOT format from FSM data."""
    
    dot_lines = [
        "digraph FSM {",
        "  rankdir=LR;",
        "  node [shape=circle];",
        "",
        "  // States"
    ]
    
    # Add states
    for state in fsm['states']:
        state_name = state['name']
        shape = "doublecircle" if state['is_final'] else "circle"
        style = "bold" if state['is_initial'] else "normal"
        
        dot_lines.append(f"  {state_name} [shape={shape}, style={style}];")
    
    dot_lines.append("")
    dot_lines.append("  // Transitions")
    
    # Add transitions
    for transition in fsm['transitions']:
        from_state = transition['from_state']
        to_state = transition['to_state']
        guard = transition.get('guard', '')
        
        # Clean up guard condition for display
        if guard:
            guard = guard.replace('"', '').replace("'", '')
            if len(guard) > 30:
                guard = guard[:27] + "..."
            label = f"{guard}"
        else:
            label = ""
        
        dot_lines.append(f"  {from_state} -> {to_state} [label=\"{label}\"];")
    
    dot_lines.append("}")
    
    return "\n".join(dot_lines)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 visualize_fsm.py <input_json> <output_svg>")
        sys.exit(1)
    
    input_json = sys.argv[1]
    output_svg = sys.argv[2]
    
    visualize_fsm_from_json(input_json, output_svg) 