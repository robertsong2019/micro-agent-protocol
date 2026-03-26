#!/usr/bin/env python3
"""
MAP CLI - Command-line interface for Micro Agent Protocol
"""

import argparse
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from map_interpreter import MAPInterpreter
from compilers.map_to_openclaw import compile_to_openclaw
from compilers.map_to_krillclaw import compile_to_krillclaw


def cmd_run(args):
    """Run a MAP workflow"""
    if not os.path.exists(args.workflow):
        print(f"Error: Workflow file not found: {args.workflow}")
        sys.exit(1)
    
    # Parse inputs
    inputs = {}
    if args.input:
        for inp in args.input:
            if '=' in inp:
                key, value = inp.split('=', 1)
                inputs[key] = value
    
    try:
        interpreter = MAPInterpreter(args.workflow)
        results = interpreter.run(inputs)
        
        print("\n" + "="*50)
        print(f"Workflow: {interpreter.workflow['name']}")
        print("="*50 + "\n")
        
        for step_id, result in results.items():
            print(f"✓ Step: {step_id}")
            print(f"  Status: {'✅ Success' if result.success else '❌ Failed'}")
            if result.output:
                print(f"  Output: {result.output}")
            if result.error:
                print(f"  Error: {result.error}")
            print()
            
    except Exception as e:
        print(f"Error running workflow: {e}")
        sys.exit(1)


def cmd_compile(args):
    """Compile MAP workflow to different targets"""
    if not os.path.exists(args.workflow):
        print(f"Error: Workflow file not found: {args.workflow}")
        sys.exit(1)
    
    if args.target == 'openclaw':
        output_dir = args.output or 'skill_output'
        compile_to_openclaw(args.workflow, output_dir)
        
    elif args.target == 'krillclaw':
        output_file = args.output or 'workflow.zig'
        compile_to_krillclaw(args.workflow, output_file)
        
    elif args.target == 'wasm':
        print("WASM target not yet implemented")
        sys.exit(1)
        
    else:
        print(f"Unknown target: {args.target}")
        print("Available targets: openclaw, krillclaw, wasm")
        sys.exit(1)


def cmd_validate(args):
    """Validate a MAP workflow"""
    if not os.path.exists(args.workflow):
        print(f"Error: Workflow file not found: {args.workflow}")
        sys.exit(1)
    
    try:
        import yaml
        with open(args.workflow) as f:
            workflow = yaml.safe_load(f)
        
        errors = []
        warnings = []
        
        # Check required fields
        if not workflow.get('version'):
            errors.append("Missing required field: version")
        elif workflow['version'] != '1.0':
            warnings.append(f"Version {workflow['version']} may not be fully supported")
        
        if not workflow.get('name'):
            errors.append("Missing required field: name")
        
        if not workflow.get('steps'):
            errors.append("Missing required field: steps")
        else:
            for i, step in enumerate(workflow['steps']):
                if 'parallel' in step:
                    for j, pstep in enumerate(step['parallel']):
                        if not pstep.get('id'):
                            errors.append(f"Parallel step {j} missing id")
                        if not pstep.get('intent'):
                            warnings.append(f"Parallel step {j} missing intent")
                else:
                    if not step.get('id'):
                        errors.append(f"Step {i} missing id")
                    if not step.get('intent'):
                        warnings.append(f"Step {i} missing intent")
        
        # Check environment variables
        env_vars = workflow.get('env', {})
        for var_name, var_value in env_vars.items():
            if var_value == 'required':
                if not os.environ.get(var_name):
                    warnings.append(f"Required env var {var_name} not set")
        
        # Print results
        print(f"\nValidating: {args.workflow}\n")
        
        if errors:
            print("❌ Errors:")
            for err in errors:
                print(f"  - {err}")
        
        if warnings:
            print("\n⚠️  Warnings:")
            for warn in warnings:
                print(f"  - {warn}")
        
        if not errors and not warnings:
            print("✅ Workflow is valid!")
        elif not errors:
            print("\n✅ Workflow is valid (with warnings)")
        else:
            print(f"\n❌ Found {len(errors)} error(s)")
            sys.exit(1)
            
    except yaml.YAMLError as e:
        print(f"YAML parsing error: {e}")
        sys.exit(1)


def cmd_init(args):
    """Initialize a new MAP workflow"""
    template = f"""version: "1.0"
name: {args.name}
description: A new MAP workflow

env:
  # API_KEY: required

steps:
  - id: step_one
    intent: "Describe what this step does"
    # tools: [http]
    # output: result
    
  - id: step_two
    intent: "Process the result"
    # input:
    #   data: {{step_one}}

# tools:
#   http:
#     type: http
#     base_url: https://api.example.com
"""
    
    filename = args.filename or f"{args.name}.map.yaml"
    
    if os.path.exists(filename) and not args.force:
        print(f"Error: File {filename} already exists. Use --force to overwrite.")
        sys.exit(1)
    
    with open(filename, 'w') as f:
        f.write(template)
    
    print(f"✅ Created new workflow: {filename}")


def main():
    parser = argparse.ArgumentParser(
        description='Micro Agent Protocol (MAP) CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  map init my-workflow                  # Create new workflow
  map validate my-workflow.map.yaml     # Validate workflow
  map run my-workflow.map.yaml          # Run workflow
  map compile -t openclaw workflow.yaml # Compile to OpenClaw skill
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run a MAP workflow')
    run_parser.add_argument('workflow', help='Path to MAP workflow file')
    run_parser.add_argument('-i', '--input', action='append', help='Input parameters (key=value)')
    run_parser.set_defaults(func=cmd_run)
    
    # Compile command
    compile_parser = subparsers.add_parser('compile', help='Compile MAP workflow')
    compile_parser.add_argument('workflow', help='Path to MAP workflow file')
    compile_parser.add_argument('-t', '--target', required=True,
                               choices=['openclaw', 'krillclaw', 'wasm'],
                               help='Target platform')
    compile_parser.add_argument('-o', '--output', help='Output path')
    compile_parser.set_defaults(func=cmd_compile)
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate MAP workflow')
    validate_parser.add_argument('workflow', help='Path to MAP workflow file')
    validate_parser.set_defaults(func=cmd_validate)
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Create new MAP workflow')
    init_parser.add_argument('name', help='Workflow name')
    init_parser.add_argument('-f', '--filename', help='Output filename')
    init_parser.add_argument('--force', action='store_true', help='Overwrite existing file')
    init_parser.set_defaults(func=cmd_init)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()
