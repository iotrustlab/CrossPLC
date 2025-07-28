#!/usr/bin/env python3
"""
Example: Export Control Flow Graph (CFG) to DOT and GraphML formats

This example demonstrates how to:
1. Load an L5X file and convert to IR
2. Generate CFG analysis
3. Export to DOT and GraphML formats for visualization
4. Show how to use the generated files with graph visualization tools
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from l5x_st_compiler.ir_converter import IRConverter
from l5x_st_compiler.export_ir import export_cfg_to_graphs, CFGAnalyzer, GraphExporter
import l5x

def main():
    """Demonstrate CFG graph export functionality."""
    
    # Example L5X file (you can change this to any L5X file)
    l5x_file = "sampledata/swatfiles/P1.L5X"
    
    print("🔍 CFG Graph Export Example")
    print("=" * 50)
    
    # Step 1: Load L5X and convert to IR
    print(f"📖 Loading L5X file: {l5x_file}")
    project = l5x.Project(l5x_file)
    
    ir_converter = IRConverter()
    ir_project = ir_converter.l5x_to_ir(project)
    
    print(f"✅ Converted to IR:")
    print(f"  - Controller: {ir_project.controller.name}")
    print(f"  - Programs: {len(ir_project.programs)}")
    print(f"  - Routines: {sum(len(p.routines) for p in ir_project.programs)}")
    
    # Step 2: Generate CFG analysis
    print(f"\n🔧 Generating CFG analysis...")
    cfg_analyzer = CFGAnalyzer()
    cfg_data = cfg_analyzer.analyze_cfg(ir_project)
    inter_routine_dataflow = cfg_analyzer.analyze_inter_routine_dataflow(ir_project)
    
    # Combine CFG data
    full_cfg_data = {
        "cfg": cfg_data,
        "inter_routine_dataflow": inter_routine_dataflow
    }
    
    print(f"✅ CFG Analysis Complete:")
    print(f"  - Routines with CFG: {len(cfg_data)}")
    print(f"  - Total blocks: {sum(len(cfg.get('blocks', [])) for cfg in cfg_data.values())}")
    print(f"  - Data flow edges: {len(inter_routine_dataflow)}")
    
    # Step 3: Export to graph formats
    print(f"\n📊 Exporting graphs...")
    graph_files = export_cfg_to_graphs(full_cfg_data, "out")
    
    print(f"✅ Generated graph files:")
    for graph_type, file_path in graph_files.items():
        print(f"  - {graph_type}: {file_path}")
    
    # Step 4: Show how to use the files
    print(f"\n🎯 How to use the generated files:")
    print(f"")
    print(f"1. DOT Files (for Graphviz):")
    print(f"   - {graph_files['cfg_dot']}: Control flow graph")
    print(f"   - {graph_files['dataflow_dot']}: Inter-routine data flow")
    print(f"   ")
    print(f"   To visualize with Graphviz:")
    print(f"   dot -Tpng {graph_files['cfg_dot']} -o cfg.png")
    print(f"   dot -Tsvg {graph_files['cfg_dot']} -o cfg.svg")
    print(f"")
    print(f"2. GraphML Files (for Gephi, NetworkX, etc.):")
    print(f"   - {graph_files['cfg_graphml']}: Control flow graph")
    print(f"   - {graph_files['dataflow_graphml']}: Inter-routine data flow")
    print(f"   ")
    print(f"   To load in Python with NetworkX:")
    print(f"   import networkx as nx")
    print(f"   G = nx.read_graphml('{graph_files['cfg_graphml']}')")
    print(f"")
    print(f"3. Visualization Tools:")
    print(f"   - Gephi: Load .graphml files")
    print(f"   - Graphviz: Render .dot files")
    print(f"   - NetworkX: Python graph analysis")
    print(f"   - yEd: Load .graphml files")
    
    # Step 5: Show a sample of the CFG structure
    print(f"\n📋 Sample CFG Structure:")
    for routine_name, routine_cfg in list(cfg_data.items())[:2]:  # Show first 2 routines
        print(f"  Routine: {routine_name}")
        blocks = routine_cfg.get("blocks", [])
        for i, block in enumerate(blocks[:3]):  # Show first 3 blocks
            block_id = block.get("block_id", "")
            block_type = block.get("type", "instruction")
            defs = block.get("defs", [])
            uses = block.get("uses", [])
            print(f"    Block {i+1}: {block_id} ({block_type})")
            if defs:
                print(f"      Defs: {defs}")
            if uses:
                print(f"      Uses: {uses}")
        if len(blocks) > 3:
            print(f"    ... and {len(blocks) - 3} more blocks")
        print(f"")
    
    print(f"🎉 CFG Graph Export Example Complete!")
    print(f"Check the 'out/' directory for generated files.")

if __name__ == "__main__":
    main() 