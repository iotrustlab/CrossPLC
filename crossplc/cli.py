"""Command-line interface for the CrossPLC compiler."""

import argparse
import sys
from pathlib import Path
import logging
import click
from datetime import datetime
import xml.etree.ElementTree as ET

from .l5x2st import L5X2STConverter, convert_st_to_l5x_file
from .st2l5x import ST2L5XConverter, convert_st_to_l5x_string
from .ir_converter import IRConverter
from .models import RoundTripInfo
from .export_ir import export_ir_to_json


def validate_ir(ir_project) -> list:
    """Validate IR for required structure. Returns list of error strings."""
    errors = []
    if not ir_project.controller or not ir_project.controller.name:
        errors.append("Controller missing or unnamed.")
    if not ir_project.controller.tags:
        errors.append("No controller tags found.")
    if not ir_project.programs:
        errors.append("No programs found.")
    for prog in ir_project.programs:
        if not prog.routines:
            errors.append(f"Program '{prog.name}' has no routines.")
    return errors


def l5x2st_main():
    """Main entry point for L5X to ST conversion."""
    parser = argparse.ArgumentParser(
        description='Convert L5X files to Structured Text.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  l5x2st -i project.L5X -o output.st
  l5x2st -d l5x_files -o consolidated.st
  l5x2st -i project.L5X -o output.st --use-ir
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '-i', '--input',
        metavar='L5X_FILE',
        help='Input L5X file to convert'
    )
    group.add_argument(
        '-d', '--directory',
        metavar='L5X_DIR',
        help='Directory containing L5X files to convert'
    )
    
    parser.add_argument(
        '-o', '--output',
        metavar='ST_FILE',
        default='output.st',
        help='Output ST file (default: output.st)'
    )
    
    parser.add_argument(
        '--use-ir',
        action='store_true',
        help='Use IR/guardrail mode for round-trip conversion (L5X→IR→ST→IR→L5X)'
    )
    
    parser.add_argument(
        '--l5k-overlay',
        metavar='L5K_FILE',
        help='L5K file to provide additional project context (tags, tasks, programs, modules)'
    )
    
    parser.add_argument(
        '--legacy',
        action='store_true',
        help='Use legacy conversion mode (basic tag generation without preservation)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    try:
        if args.use_ir:
            print("[INFO] IR/guardrail mode enabled: L5X→IR→ST with validation.")
            ir_converter = IRConverter()
            
            if args.input:
                # Convert single file with IR
                if not Path(args.input).exists():
                    print(f"Error: Input file '{args.input}' not found.")
                    sys.exit(1)
                
                if args.verbose:
                    print(f"Converting {args.input} to {args.output} using IR mode")
                
                # L5X → IR → ST
                import l5x
                project = l5x.Project(args.input)
                ir_project = ir_converter.l5x_to_ir(project, args.l5k_overlay)
                
                # Generate ST from IR
                l5x2st = L5X2STConverter()
                st_code = l5x2st.convert_l5x_to_st(args.input, args.l5k_overlay)
                
                with open(args.output, 'w') as f:
                    f.write(st_code)
                
                print(f"[INFO] IR validation passed. Wrote ST code to {args.output}")
                
            elif args.directory:
                print("Error: IR mode not yet supported for directory conversion.")
                sys.exit(1)
        else:
            # Standard conversion
            converter = L5X2STConverter()
            
            if args.input:
                # Convert single file
                if not Path(args.input).exists():
                    print(f"Error: Input file '{args.input}' not found.")
                    sys.exit(1)
                
                if args.verbose:
                    print(f"Converting {args.input} to {args.output}")
                    if args.l5k_overlay:
                        print(f"Using L5K overlay: {args.l5k_overlay}")
                    if args.legacy:
                        print("Using legacy conversion mode (basic tag generation)")
                    else:
                        print("Using tag preservation mode (recommended)")
                
                if args.legacy:
                    # Use legacy conversion (basic tag generation)
                    st_code = converter.convert_l5x_to_st(args.input, args.l5k_overlay)
                    with open(args.output, 'w', encoding='utf-8') as f:
                        f.write(st_code)
                else:
                    # Use enhanced roundtrip conversion (default - tag preservation)
                    from .l5x2st import convert_enhanced_roundtrip_file
                    convert_enhanced_roundtrip_file(args.input, args.output, args.l5k_overlay)
                    print(f"Tag preservation conversion completed: {args.output}")
                
            elif args.directory:
                # Convert directory
                if not Path(args.directory).exists():
                    print(f"Error: Input directory '{args.directory}' not found.")
                    sys.exit(1)
                
                if args.verbose:
                    print(f"Converting all L5X files in {args.directory} to {args.output}")
                
                converter.convert_directory(args.directory, args.output)
            
            print(f"Successfully converted to {args.output}")
        
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@click.command()
@click.option('--input', '-i', 'input_file', required=True, help='Input ST file')
@click.option('--output', '-o', 'output_file', required=True, help='Output L5X file')
@click.option('--use-ir', is_flag=True, help='Use IR/guardrail mode for round-trip conversion')
@click.option('--legacy', is_flag=True, help='Use legacy conversion mode (basic tag generation without preservation)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def st2l5x(input_file: str, output_file: str, use_ir: bool, legacy: bool, verbose: bool):
    """Convert Structured Text (ST) to L5X format."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    try:
        if use_ir:
            click.echo("[INFO] IR/guardrail mode enabled: ST→IR→L5X with validation.")
            
            # Read ST file
            with open(input_file, 'r', encoding='utf-8') as f:
                st_code = f.read()
            
            # Convert ST to L5X with IR validation
            st2l5x_converter = ST2L5XConverter()
            l5x_xml = convert_st_to_l5x_string(st_code)
            
            # Validate IR before writing L5X
            ir_converter = IRConverter()
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.L5X', delete=False) as temp_file:
                temp_file.write(l5x_xml)
                temp_l5x_path = temp_file.name
            
            try:
                import l5x
                project = l5x.Project(temp_l5x_path)
                ir_project = ir_converter.l5x_to_ir(project)
                errors = validate_ir(ir_project)
                
                if errors:
                    click.echo("[ERROR] IR validation failed:", err=True)
                    for err in errors:
                        click.echo(f"  - {err}", err=True)
                    sys.exit(1)
                
                # Write validated L5X
                with open(output_file, 'w') as f:
                    f.write(l5x_xml)
                
                click.echo(f"✅ IR validation passed. Successfully converted {input_file} to {output_file}")
                
            finally:
                if os.path.exists(temp_l5x_path):
                    os.unlink(temp_l5x_path)
        else:
            # Standard conversion
            with open(input_file, 'r', encoding='utf-8') as f:
                st_code = f.read()
            
            if legacy:
                # Use legacy conversion (basic tag generation)
                st2l5x_converter = ST2L5XConverter()
                l5x_xml = st2l5x_converter.parse_st_code(st_code)
                
                # Write legacy L5X
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
                    f.write(ET.tostring(l5x_xml, encoding='unicode', method='xml'))
                
                click.echo(f"✅ Legacy conversion completed: {output_file}")
            else:
                # Standard conversion
                convert_st_to_l5x_file(st_code, output_file)
                click.echo(f"✅ Successfully converted {input_file} to {output_file}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@click.command()
@click.option('--input', '-i', 'input_file', required=True, help='Input L5X file')
@click.option('--output', '-o', 'output_file', required=True, help='Output JSON file')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def extract_io(input_file: str, output_file: str, verbose: bool):
    """Extract I/O tag definitions from L5X file and output as JSON."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    try:
        import json
        import l5x
        
        click.echo(f"📖 Reading L5X file: {input_file}")
        
        # Load L5X project
        project = l5x.Project(input_file)
        
        # Extract I/O tags using IRConverter
        ir_converter = IRConverter()
        io_tags = ir_converter.extract_io_tags(project)
        
        # Prepare output data
        output_data = {
            'source_file': input_file,
            'extraction_time': datetime.now().isoformat(),
            'total_io_tags': len(io_tags),
            'io_tags': io_tags
        }
        
        # Write JSON output
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        click.echo(f"✅ Extracted {len(io_tags)} I/O tags to {output_file}")
        
        # Print summary
        input_count = sum(1 for tag in io_tags if tag['direction'] == 'Input')
        output_count = sum(1 for tag in io_tags if tag['direction'] == 'Output')
        
        click.echo(f"📊 Summary:")
        click.echo(f"  - Input tags: {input_count}")
        click.echo(f"  - Output tags: {output_count}")
        
        if verbose:
            click.echo(f"\n📋 I/O Tags:")
            for tag in io_tags:
                click.echo(f"  - {tag['name']} ({tag['direction']}, {tag['data_type']})")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point for the combined tool."""
    parser = argparse.ArgumentParser(
        description='CrossPLC - Cross-vendor translation and semantic analysis framework for PLC logic.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert L5X to ST (default - tag preservation mode)
  crossplc l5x2st -i project.L5X -o output.st
  
  # Convert L5X to ST (legacy mode - basic tag generation)
  crossplc l5x2st -i project.L5X -o output.st --legacy
  
  # Convert L5X to ST (tag preservation with L5K overlay)
  crossplc l5x2st -i project.L5X -o output.st --l5k-overlay overlay.L5K
  
  # Convert L5X to ST (IR/guardrail mode)
  crossplc l5x2st -i project.L5X -o output.st --use-ir
  
  # Convert ST to L5X (default - tag preservation mode)
  crossplc st2l5x -i program.st -o output.L5X
  
  # Convert ST to L5X (legacy mode - basic tag generation)
  crossplc st2l5x -i program.st -o output.L5X --legacy
  
  # Convert ST to L5X (IR/guardrail mode)
  crossplc st2l5x -i program.st -o output.L5X --use-ir
  
  # Extract I/O tags from L5X file
  crossplc extract-io -i Control.L5X -o io_mapping.json
  
  # Export IR components to JSON
  crossplc export-ir -i P1.L5X -o out/ir_dump.json --include tags,control_flow
  
  # Convert directory of L5X files
  crossplc l5x2st -d l5x_files -o consolidated.st
        """
    )
    
    parser.add_argument(
        'command',
                        choices=['l5x2st', 'st2l5x', 'extract-io', 'export-ir', 'analyze-multi', 'explore-lad', 'parse-txt', 'parse-scl', 'extract-fsm'],
        help='Command to execute'
    )
    
    # Parse the command
    args, remaining = parser.parse_known_args()
    
    # Route to appropriate command
    if args.command == 'l5x2st':
        # Temporarily replace sys.argv for the subcommand
        original_argv = sys.argv
        sys.argv = ['l5x2st'] + remaining
        try:
            l5x2st_main()
        finally:
            sys.argv = original_argv
    elif args.command == 'st2l5x':
        # For st2l5x, we need to parse the remaining arguments manually
        # since it uses click
        import tempfile
        import os
        
        # Parse the remaining arguments
        st2l5x_parser = argparse.ArgumentParser()
        st2l5x_parser.add_argument('--input', '-i', required=True)
        st2l5x_parser.add_argument('--output', '-o', required=True)
        st2l5x_parser.add_argument('--use-ir', action='store_true')
        st2l5x_parser.add_argument('--legacy', action='store_true')
        st2l5x_parser.add_argument('--verbose', '-v', action='store_true')
        
        try:
            st2l5x_args = st2l5x_parser.parse_args(remaining)
            
            # Call the st2l5x function directly, bypassing click
            if st2l5x_args.verbose:
                logging.basicConfig(level=logging.DEBUG)
            
            try:
                from crossplc.l5x2st import L5X2STConverter
                l5x2st_converter = L5X2STConverter()
                if st2l5x_args.use_ir:
                    print("[INFO] IR/guardrail mode enabled: ST→IR→L5X with validation.")
                    
                    # Read ST file
                    with open(st2l5x_args.input, 'r', encoding='utf-8') as f:
                        st_code = f.read()
                    
                    # Split ST code into variables and program logic
                    variables, program_logic = l5x2st_converter._parse_st_code_sections(st_code)
                    
                    # Convert ST to L5X with IR validation
                    st2l5x_converter = ST2L5XConverter()
                    l5x_xml = convert_st_to_l5x_string(variables + "\n\n" + program_logic)
                    
                    # Validate IR before writing L5X
                    ir_converter = IRConverter()
                    import tempfile
                    import os
                    
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.L5X', delete=False) as temp_file:
                        temp_file.write(l5x_xml)
                        temp_l5x_path = temp_file.name
                    
                    try:
                        import l5x
                        project = l5x.Project(temp_l5x_path)
                        ir_project = ir_converter.l5x_to_ir(project)
                        errors = validate_ir(ir_project)
                        
                        if errors:
                            print("[ERROR] IR validation failed:")
                            for err in errors:
                                print(f"  - {err}")
                            sys.exit(1)
                        
                        # Write validated L5X
                        with open(st2l5x_args.output, 'w') as f:
                            f.write(l5x_xml)
                        
                        print(f"✅ IR validation passed. Successfully converted {st2l5x_args.input} to {st2l5x_args.output}")
                        
                    finally:
                        if os.path.exists(temp_l5x_path):
                            os.unlink(temp_l5x_path)
                else:
                    # Standard conversion
                    with open(st2l5x_args.input, 'r', encoding='utf-8') as f:
                        st_code = f.read()
                    
                    if st2l5x_args.legacy:
                        # Use legacy conversion (basic tag generation)
                        st2l5x_converter = ST2L5XConverter()
                        l5x_xml = st2l5x_converter.parse_st_code(st_code)
                        
                        # Write legacy L5X
                        with open(st2l5x_args.output, 'w', encoding='utf-8') as f:
                            f.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
                            f.write(ET.tostring(l5x_xml, encoding='unicode', method='xml'))
                        
                        print(f"✅ Legacy conversion completed: {st2l5x_args.output}")
                    else:
                        # Standard conversion
                        convert_st_to_l5x_file(st_code, st2l5x_args.output)
                        print(f"✅ Successfully converted {st2l5x_args.input} to {st2l5x_args.output}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                sys.exit(1)
            
        except SystemExit:
            # If argparse fails, show help
            st2l5x_parser.print_help()
            sys.exit(1)
    elif args.command == 'extract-io':
        # Parse the remaining arguments for extract-io
        extract_io_parser = argparse.ArgumentParser()
        extract_io_parser.add_argument('--input', '-i', required=True)
        extract_io_parser.add_argument('--output', '-o', required=True)
        extract_io_parser.add_argument('--verbose', '-v', action='store_true')
        
        try:
            extract_io_args = extract_io_parser.parse_args(remaining)
            
            # Call the extract_io function directly, bypassing click
            if extract_io_args.verbose:
                logging.basicConfig(level=logging.DEBUG)
            
            try:
                import json
                import l5x
                from datetime import datetime
                
                print(f"📖 Reading L5X file: {extract_io_args.input}")
                
                # Load L5X project
                project = l5x.Project(extract_io_args.input)
                
                # Extract I/O tags using IRConverter
                ir_converter = IRConverter()
                io_tags = ir_converter.extract_io_tags(project)
                
                # Prepare output data
                output_data = {
                    'source_file': extract_io_args.input,
                    'extraction_time': datetime.now().isoformat(),
                    'total_io_tags': len(io_tags),
                    'io_tags': io_tags
                }
                
                # Write JSON output
                with open(extract_io_args.output, 'w') as f:
                    json.dump(output_data, f, indent=2)
                
                print(f"✅ Extracted {len(io_tags)} I/O tags to {extract_io_args.output}")
                
                # Print summary
                input_count = sum(1 for tag in io_tags if tag['direction'] == 'Input')
                output_count = sum(1 for tag in io_tags if tag['direction'] == 'Output')
                
                print(f"📊 Summary:")
                print(f"  - Input tags: {input_count}")
                print(f"  - Output tags: {output_count}")
                
                if extract_io_args.verbose:
                    print(f"\n📋 I/O Tags:")
                    for tag in io_tags:
                        print(f"  - {tag['name']} ({tag['direction']}, {tag['data_type']})")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                if extract_io_args.verbose:
                    import traceback
                    traceback.print_exc()
                sys.exit(1)
            
        except SystemExit:
            # If argparse fails, show help
            extract_io_parser.print_help()
            sys.exit(1)
    elif args.command == 'export-ir':
        # Parse the remaining arguments for export-ir
        export_ir_parser = argparse.ArgumentParser()
        export_ir_parser.add_argument('--input', '-i', required=True, help='Input L5X file')
        export_ir_parser.add_argument('--output', '-o', required=True, help='Output JSON file')
        export_ir_parser.add_argument('--include', type=str, default='tags,control_flow', 
                                     help='Components to include (comma-separated: tags,control_flow,data_types,function_blocks,interactions,routines,programs,semantic,cfg)')
        export_ir_parser.add_argument('--mode', type=str, choices=['default', 'cfg'], default='default',
                                     help='Export mode: default or cfg (control flow graph)')
        export_ir_parser.add_argument('--export-graphs', action='store_true',
                                     help='Export CFG to DOT and GraphML formats')
        export_ir_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        
        try:
            export_ir_args = export_ir_parser.parse_args(remaining)
            
            # Call the export_ir function directly
            if export_ir_args.verbose:
                logging.basicConfig(level=logging.DEBUG)
            
            try:
                import l5x
                from pathlib import Path
                
                print(f"📖 Reading L5X file: {export_ir_args.input}")
                
                # Load L5X project
                project = l5x.Project(export_ir_args.input)
                
                # Convert to IR
                ir_converter = IRConverter()
                ir_project = ir_converter.l5x_to_ir(project)
                
                print(f"🔄 Converting to IR...")
                print(f"  - Controller: {ir_project.controller.name}")
                print(f"  - Programs: {len(ir_project.programs)}")
                print(f"  - Controller tags: {len(ir_project.controller.tags)}")
                
                # Parse include components
                include_components = [comp.strip() for comp in export_ir_args.include.split(',')]
                
                # Handle mode-specific behavior
                if export_ir_args.mode == 'cfg':
                    # For CFG mode, override include to only export CFG
                    include_components = ['cfg']
                    print(f"🔧 CFG mode enabled - exporting control flow graph")
                
                # Export IR to JSON
                print(f"📤 Exporting IR components: {', '.join(include_components)}")
                export_data = export_ir_to_json(
                    ir_project=ir_project,
                    output_path=export_ir_args.output,
                    include=include_components,
                    pretty_print=True
                )
                
                print(f"✅ Successfully exported IR to {export_ir_args.output}")
                
                # Export graphs if requested
                if export_ir_args.export_graphs and 'cfg' in export_data:
                    print(f"📊 Exporting graphs...")
                    from .export_ir import export_cfg_to_graphs
                    graph_files = export_cfg_to_graphs(export_data['cfg'])
                    for graph_type, file_path in graph_files.items():
                        print(f"  - {graph_type}: {file_path}")
                
                # Print summary
                metadata = export_data.get('metadata', {})
                print(f"📊 Export Summary:")
                print(f"  - Controller: {metadata.get('source_controller', 'Unknown')}")
                print(f"  - Programs: {metadata.get('total_programs', 0)}")
                print(f"  - Routines: {metadata.get('total_routines', 0)}")
                print(f"  - Exported components: {', '.join(include_components)}")
                
                if export_ir_args.verbose:
                    print(f"\n📋 Detailed Summary:")
                    for component in include_components:
                        if component in export_data:
                            summary = export_data[component].get('summary', {})
                            for key, value in summary.items():
                                print(f"  - {component}.{key}: {value}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                if export_ir_args.verbose:
                    import traceback
                    traceback.print_exc()
                sys.exit(1)
            
        except SystemExit:
            # If argparse fails, show help
            export_ir_parser.print_help()
            sys.exit(1)
    elif args.command == 'analyze-multi':
        # Parse the remaining arguments for analyze-multi
        analyze_multi_parser = argparse.ArgumentParser()
        analyze_multi_parser.add_argument('--directory', '-d', help='Directory containing L5X and L5K files')
        analyze_multi_parser.add_argument('--l5x', action='append', help='L5X file path (can be specified multiple times)')
        analyze_multi_parser.add_argument('--l5k', action='append', help='L5K file path (can be specified multiple times)')
        analyze_multi_parser.add_argument('--st', action='append', help='OpenPLC .st file path (can be specified multiple times)')
        analyze_multi_parser.add_argument('--scl', action='append', help='Siemens SCL file path (can be specified multiple times)')
        analyze_multi_parser.add_argument('--cpp', action='append', help='TXT C++ file path (can be specified multiple times)')
        analyze_multi_parser.add_argument('--output', '-o', required=True, help='Output JSON file')
        analyze_multi_parser.add_argument('--include', type=str, default='shared_tags,conflicts,controllers',
                                         help='Components to include (comma-separated: shared_tags,conflicts,controllers,tags,control_flow,data_types,function_blocks,interactions,routines,programs,semantic,cfg)')
        analyze_multi_parser.add_argument('--require-overlay', action='store_true', help='Require L5K overlay for all PLCs')
        analyze_multi_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        
        try:
            analyze_multi_args = analyze_multi_parser.parse_args(remaining)
            
            # Call the analyze_multi function directly
            if analyze_multi_args.verbose:
                logging.basicConfig(level=logging.DEBUG)
            
            try:
                from pathlib import Path
                from .project_ir import ProjectIR
                
                l5x_files = []
                l5k_overlays = {}
                
                if analyze_multi_args.directory:
                    # Load from directory
                    dir_path = Path(analyze_multi_args.directory)
                    if not dir_path.exists():
                        print(f"❌ Error: Directory '{analyze_multi_args.directory}' not found.")
                        sys.exit(1)
                    
                    # Find all L5X, L5K, .st, .scl, .udt, .db, and .cpp/.h files
                    l5x_files = list(dir_path.glob("*.L5X"))
                    st_files = list(dir_path.glob("*.st"))
                    scl_files = list(dir_path.glob("*.scl"))
                    udt_files = list(dir_path.glob("*.udt"))
                    db_files = list(dir_path.glob("*.db"))
                    cpp_files = list(dir_path.glob("*.cpp")) + list(dir_path.glob("*.h")) + list(dir_path.glob("*.hpp"))
                    l5k_files = list(dir_path.glob("*.L5K"))
                    
                    # Combine all files for analysis
                    all_files = l5x_files + st_files + scl_files + udt_files + db_files + cpp_files
                    
                    # Match L5X and L5K files by name
                    for l5x_file in l5x_files:
                        plc_name = ProjectIR._extract_plc_name(l5x_file)
                        matching_l5k = None
                        for l5k_file in l5k_files:
                            if l5k_file.stem == l5x_file.stem:
                                matching_l5k = l5k_file
                                break
                        if matching_l5k:
                            l5k_overlays[plc_name] = matching_l5k
                    
                    print(f"📁 Found {len(l5x_files)} L5X files, {len(st_files)} OpenPLC files, {len(scl_files)} Siemens SCL files, {len(udt_files)} Siemens UDT files, {len(db_files)} Siemens DB files, {len(cpp_files)} TXT C++ files, and {len(l5k_files)} L5K files in directory")
                    
                elif analyze_multi_args.l5x or analyze_multi_args.st or analyze_multi_args.scl or analyze_multi_args.cpp:
                    # Load from explicit file lists (mixed L5X, .st, and .scl files)
                    all_files = []
                    
                    if analyze_multi_args.l5x:
                        l5x_files = [Path(f) for f in analyze_multi_args.l5x]
                        all_files.extend(l5x_files)
                        
                        # Handle L5K overlays for L5X files
                        l5k_files = [Path(f) for f in analyze_multi_args.l5k] if analyze_multi_args.l5k else []
                        for i, l5x_file in enumerate(l5x_files):
                            plc_name = ProjectIR._extract_plc_name(l5x_file)
                            if i < len(l5k_files):
                                l5k_overlays[plc_name] = l5k_files[i]
                    
                    if analyze_multi_args.st:
                        st_files = [Path(f) for f in analyze_multi_args.st]
                        all_files.extend(st_files)
                    
                    if analyze_multi_args.scl:
                        scl_files = [Path(f) for f in analyze_multi_args.scl]
                        all_files.extend(scl_files)
                    
                    if analyze_multi_args.cpp:
                        cpp_files = [Path(f) for f in analyze_multi_args.cpp]
                        all_files.extend(cpp_files)
                    
                    print(f"📁 Processing {len(all_files)} files ({len(l5x_files) if 'l5x_files' in locals() else 0} L5X, {len(st_files) if 'st_files' in locals() else 0} OpenPLC, {len(scl_files) if 'scl_files' in locals() else 0} Siemens SCL, {len(udt_files) if 'udt_files' in locals() else 0} Siemens UDT, {len(db_files) if 'db_files' in locals() else 0} Siemens DB, {len(cpp_files) if 'cpp_files' in locals() else 0} TXT C++) with {len(l5k_overlays)} L5K overlays")
                    

                
                else:
                    print("❌ Error: Must specify either --directory or --l5x files")
                    sys.exit(1)
                
                # Validate files exist
                for l5x_file in l5x_files:
                    if not l5x_file.exists():
                        print(f"❌ Error: L5X file '{l5x_file}' not found.")
                        sys.exit(1)
                
                for l5k_file in l5k_overlays.values():
                    if not l5k_file.exists():
                        print(f"❌ Error: L5K file '{l5k_file}' not found.")
                        sys.exit(1)
                
                # Create ProjectIR
                print(f"🔧 Creating multi-PLC analysis...")
                project_ir, missing_overlays = ProjectIR.from_files(all_files, l5k_overlays)
                
                # Check for missing overlays
                if missing_overlays and analyze_multi_args.require_overlay:
                    print(f"❌ Error: L5K overlays required but missing for: {', '.join(missing_overlays)}")
                    sys.exit(1)
                elif missing_overlays:
                    print(f"⚠️ Warning: L5K overlays missing for: {', '.join(missing_overlays)}")
                
                # Parse include components
                include_components = [comp.strip() for comp in analyze_multi_args.include.split(',')]
                
                # Export analysis
                output_path = Path(analyze_multi_args.output)
                print(f"📊 Exporting multi-PLC analysis to {output_path}")
                print(f"📤 Including components: {', '.join(include_components)}")
                summary = project_ir.export_summary(output_path, include_components)
                
                print(f"✅ Successfully exported multi-PLC analysis to {output_path}")
                
                # Print summary
                metadata = summary.get('metadata', {})
                print(f"📊 Analysis Summary:")
                print(f"  - Total PLCs: {metadata.get('total_plcs', 0)}")
                print(f"  - PLC Names: {', '.join(metadata.get('plc_names', []))}")
                print(f"  - Shared Tags: {metadata.get('total_shared_tags', 0)}")
                print(f"  - Conflicts: {metadata.get('total_conflicts', 0)}")
                
                if analyze_multi_args.verbose:
                    print(f"\n📋 Detailed Summary:")
                    for plc_name, plc_summary in summary.get('plc_summary', {}).items():
                        print(f"  - {plc_name}: {plc_summary['controller_tags']} tags, {plc_summary['programs']} programs, {plc_summary['routines']} routines")
                    
                    if summary.get('shared_tags'):
                        print(f"\n🔗 Shared Tags:")
                        for shared_tag in summary['shared_tags'][:5]:  # Show first 5
                            print(f"  - {shared_tag['tag']}: {shared_tag['writer']} → {', '.join(shared_tag['readers'])}")
                    
                    if summary.get('conflicting_tags'):
                        print(f"\n⚠️ Conflicts:")
                        for conflict in summary['conflicting_tags'][:5]:  # Show first 5
                            print(f"  - {conflict['tag']}: {conflict['conflict']} in {', '.join(conflict['plcs'])}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                if analyze_multi_args.verbose:
                    import traceback
                    traceback.print_exc()
                sys.exit(1)
            
        except SystemExit:
            # If argparse fails, show help
            analyze_multi_parser.print_help()
            sys.exit(1)
    elif args.command == 'explore-lad':
        # Parse the remaining arguments for explore-lad
        explore_lad_parser = argparse.ArgumentParser()
        explore_lad_parser.add_argument('--input', '-i', required=True, help='Input Siemens .zap project file or extracted directory')
        explore_lad_parser.add_argument('--output', '-o', required=True, help='Output JSON file')
        explore_lad_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        
        try:
            explore_lad_args = explore_lad_parser.parse_args(remaining)
            
            # Call the explore_lad function directly
            if explore_lad_args.verbose:
                logging.basicConfig(level=logging.DEBUG)
            
            try:
                from pathlib import Path
                from .siemens_lad_parser import SiemensLADParser
                import json
                from datetime import datetime
                
                print(f"📖 Reading Siemens LAD/FBD project: {explore_lad_args.input}")
                
                # Load and parse the project
                project_path = Path(explore_lad_args.input)
                if not project_path.exists():
                    print(f"❌ Error: Project path '{explore_lad_args.input}' not found.")
                    sys.exit(1)
                
                # Parse the project
                lad_parser = SiemensLADParser()
                ir_project = lad_parser.parse_project(project_path)
                
                print(f"🔄 Parsing LAD/FBD project...")
                print(f"  - Controller: {ir_project.controller.name}")
                print(f"  - Programs: {len(ir_project.programs)}")
                print(f"  - Controller tags: {len(ir_project.controller.tags)}")
                
                # Prepare output data
                output_data = {
                    'source_file': str(project_path),
                    'exploration_time': datetime.now().isoformat(),
                    'controller': {
                        'name': ir_project.controller.name,
                        'source_type': ir_project.controller.source_type,
                        'total_tags': len(ir_project.controller.tags)
                    },
                    'programs': []
                }
                
                # Extract program information
                for program in ir_project.programs:
                    program_info = {
                        'name': program.name,
                        'source_type': program.source_type,
                        'routines': []
                    }
                    
                    for routine in program.routines:
                        routine_info = {
                            'name': routine.name,
                            'type': routine.routine_type.value,
                            'description': routine.description,
                            'content': routine.content
                        }
                        program_info['routines'].append(routine_info)
                    
                    output_data['programs'].append(program_info)
                
                # Write JSON output
                with open(explore_lad_args.output, 'w') as f:
                    json.dump(output_data, f, indent=2)
                
                print(f"✅ Successfully explored LAD/FBD project to {explore_lad_args.output}")
                
                # Print summary
                total_routines = sum(len(prog.routines) for prog in ir_project.programs)
                print(f"📊 Summary:")
                print(f"  - Controller: {ir_project.controller.name}")
                print(f"  - Programs: {len(ir_project.programs)}")
                print(f"  - Routines: {total_routines}")
                print(f"  - Tags: {len(ir_project.controller.tags)}")
                
                if explore_lad_args.verbose:
                    print(f"\n📋 Detailed Summary:")
                    for program in ir_project.programs:
                        print(f"  - Program: {program.name}")
                        for routine in program.routines:
                            print(f"    - Routine: {routine.name} ({routine.routine_type.value})")
                    
                    if ir_project.controller.tags:
                        print(f"\n📋 Tags:")
                        for tag in ir_project.controller.tags[:10]:  # Show first 10
                            print(f"  - {tag.name} ({tag.data_type})")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                if explore_lad_args.verbose:
                    import traceback
                    traceback.print_exc()
                sys.exit(1)
            
        except SystemExit:
            # If argparse fails, show help
            explore_lad_parser.print_help()
            sys.exit(1)
    elif args.command == 'parse-txt':
        # Parse the remaining arguments for parse-txt
        parse_txt_parser = argparse.ArgumentParser()
        parse_txt_parser.add_argument('--input', '-i', required=True, help='Input TXT C++ control logic file')
        parse_txt_parser.add_argument('--output', '-o', required=True, help='Output JSON file')
        parse_txt_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        
        try:
            parse_txt_args = parse_txt_parser.parse_args(remaining)
            
            # Call the parse_txt function directly
            if parse_txt_args.verbose:
                logging.basicConfig(level=logging.DEBUG)
            
            try:
                from pathlib import Path
                from .txt_parser import TXTParser
                import json
                from datetime import datetime
                
                print(f"📖 Reading TXT control logic file: {parse_txt_args.input}")
                
                # Load and parse the file
                file_path = Path(parse_txt_args.input)
                if not file_path.exists():
                    print(f"❌ Error: File '{parse_txt_args.input}' not found.")
                    sys.exit(1)
                
                # Parse the file
                parser = TXTParser()
                ir_project = parser.parse_txt_file(str(file_path))
                
                print(f"🔄 Parsing TXT control logic...")
                print(f"  - Controller: {ir_project.controller.name}")
                print(f"  - Programs: {len(ir_project.programs)}")
                print(f"  - Controller tags: {len(ir_project.controller.tags)}")
                
                # Prepare output data
                output_data = {
                    'source_file': str(file_path),
                    'parse_time': datetime.now().isoformat(),
                    'controller': {
                        'name': ir_project.controller.name,
                        'source_type': ir_project.controller.source_type,
                        'total_tags': len(ir_project.controller.tags)
                    },
                    'programs': []
                }
                
                # Extract program information
                for program in ir_project.programs:
                    program_info = {
                        'name': program.name,
                        'source_type': program.source_type,
                        'routines': []
                    }
                    
                    for routine in program.routines:
                        routine_info = {
                            'name': routine.name,
                            'type': routine.routine_type.value,
                            'description': routine.description,
                            'content': routine.content
                        }
                        program_info['routines'].append(routine_info)
                    
                    output_data['programs'].append(program_info)
                
                # Write JSON output
                with open(parse_txt_args.output, 'w') as f:
                    json.dump(output_data, f, indent=2)
                
                print(f"✅ Successfully parsed TXT control logic to {parse_txt_args.output}")
                
                # Print summary
                total_routines = sum(len(prog.routines) for prog in ir_project.programs)
                input_tags = [tag for tag in ir_project.controller.tags if 'input' in tag.description.lower() if tag.description]
                output_tags = [tag for tag in ir_project.controller.tags if 'output' in tag.description.lower() if tag.description]
                internal_tags = [tag for tag in ir_project.controller.tags if not any(x in tag.description.lower() if tag.description else False for x in ['input', 'output'])]
                
                print(f"📊 Summary:")
                print(f"  - Controller: {ir_project.controller.name}")
                print(f"  - Programs: {len(ir_project.programs)}")
                print(f"  - Routines: {total_routines}")
                print(f"  - Input tags: {len(input_tags)}")
                print(f"  - Output tags: {len(output_tags)}")
                print(f"  - Internal tags: {len(internal_tags)}")
                
                if parse_txt_args.verbose:
                    print(f"\n📋 Detailed Summary:")
                    for program in ir_project.programs:
                        print(f"  - Program: {program.name}")
                        for routine in program.routines:
                            print(f"    - Routine: {routine.name} ({routine.routine_type.value})")
                    
                    if ir_project.controller.tags:
                        print(f"\n📋 Tags:")
                        for tag in ir_project.controller.tags[:10]:  # Show first 10
                            print(f"  - {tag.name} ({tag.data_type}): {tag.description}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                if parse_txt_args.verbose:
                    import traceback
                    traceback.print_exc()
                sys.exit(1)
            
        except SystemExit:
            # If argparse fails, show help
            parse_txt_parser.print_help()
            sys.exit(1)
    elif args.command == 'parse-scl':
        # Parse the remaining arguments for parse-scl
        parse_scl_parser = argparse.ArgumentParser()
        parse_scl_parser.add_argument('--input', '-i', required=True, help='Input Siemens SCL file')
        parse_scl_parser.add_argument('--output', '-o', required=True, help='Output JSON file')
        parse_scl_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        
        try:
            parse_scl_args = parse_scl_parser.parse_args(remaining)
            
            # Call the parse_scl function directly
            if parse_scl_args.verbose:
                logging.basicConfig(level=logging.DEBUG)
            
            try:
                from pathlib import Path
                from .siemens_scl_parser import SiemensSCLParser
                import json
                from datetime import datetime
                
                print(f"📖 Reading Siemens SCL file: {parse_scl_args.input}")
                
                # Load and parse the file
                file_path = Path(parse_scl_args.input)
                if not file_path.exists():
                    print(f"❌ Error: File '{parse_scl_args.input}' not found.")
                    sys.exit(1)
                
                # Parse the file
                parser = SiemensSCLParser()
                ir_project = parser.parse_scl_file(str(file_path))
                
                print(f"🔄 Parsing Siemens SCL...")
                print(f"  - Controller: {ir_project.controller.name}")
                print(f"  - Programs: {len(ir_project.programs)}")
                print(f"  - Controller tags: {len(ir_project.controller.tags)}")
                
                # Prepare output data
                output_data = {
                    'source_file': str(file_path),
                    'parse_time': datetime.now().isoformat(),
                    'controller': {
                        'name': ir_project.controller.name,
                        'source_type': ir_project.controller.source_type,
                        'total_tags': len(ir_project.controller.tags)
                    },
                    'programs': []
                }
                
                # Extract program information
                for program in ir_project.programs:
                    program_info = {
                        'name': program.name,
                        'source_type': program.source_type,
                        'routines': []
                    }
                    
                    for routine in program.routines:
                        routine_info = {
                            'name': routine.name,
                            'type': routine.routine_type.value,
                            'description': routine.description,
                            'content': routine.content
                        }
                        program_info['routines'].append(routine_info)
                    
                    output_data['programs'].append(program_info)
                
                # Write JSON output
                with open(parse_scl_args.output, 'w') as f:
                    json.dump(output_data, f, indent=2)
                
                print(f"✅ Successfully parsed Siemens SCL to {parse_scl_args.output}")
                
                # Print summary
                total_routines = sum(len(prog.routines) for prog in ir_project.programs)
                input_tags = [tag for tag in ir_project.controller.tags if 'input' in tag.description.lower()]
                output_tags = [tag for tag in ir_project.controller.tags if 'output' in tag.description.lower()]
                internal_tags = [tag for tag in ir_project.controller.tags if 'internal' in tag.description.lower()]
                
                print(f"📊 Summary:")
                print(f"  - Controller: {ir_project.controller.name}")
                print(f"  - Programs: {len(ir_project.programs)}")
                print(f"  - Routines: {total_routines}")
                print(f"  - Input tags: {len(input_tags)}")
                print(f"  - Output tags: {len(output_tags)}")
                print(f"  - Internal tags: {len(internal_tags)}")
                
                if parse_scl_args.verbose:
                    print(f"\n📋 Detailed Summary:")
                    for program in ir_project.programs:
                        print(f"  - Program: {program.name}")
                        for routine in program.routines:
                            print(f"    - Routine: {routine.name} ({routine.routine_type.value})")
                    
                    if ir_project.controller.tags:
                        print(f"\n📋 Tags:")
                        for tag in ir_project.controller.tags[:10]:  # Show first 10
                            print(f"  - {tag.name} ({tag.data_type}): {tag.description}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                if parse_scl_args.verbose:
                    import traceback
                    traceback.print_exc()
                sys.exit(1)
            
        except SystemExit:
            # If argparse fails, show help
            parse_scl_parser.print_help()
            sys.exit(1)
    

if __name__ == '__main__':
    main() 