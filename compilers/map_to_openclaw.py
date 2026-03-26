#!/usr/bin/env python3
"""
MAP to OpenClaw Skill Compiler
Converts MAP workflow to OpenClaw skill format
"""

import yaml
import json
import os
from pathlib import Path
from typing import Dict, Any


class OpenClawCompiler:
    """Compiles MAP workflows to OpenClaw skill format"""
    
    def __init__(self, workflow: Dict[str, Any]):
        self.workflow = workflow
        
    def compile(self, output_dir: str) -> None:
        """Generate OpenClaw skill directory"""
        skill_dir = Path(output_dir)
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate SKILL.md
        skill_md = self._generate_skill_md()
        (skill_dir / "SKILL.md").write_text(skill_md)
        
        # Generate skill.json
        skill_json = self._generate_skill_json()
        (skill_dir / "skill.json").write_text(json.dumps(skill_json, indent=2))
        
        # Generate AGENTS.md if steps need context
        if self.workflow.get('steps'):
            agents_md = self._generate_agents_md()
            (skill_dir / "AGENTS.md").write_text(agents_md)
        
        print(f"✅ OpenClaw skill generated at: {skill_dir}")
    
    def _generate_skill_md(self) -> str:
        """Generate SKILL.md content"""
        name = self.workflow.get('name', 'unnamed')
        description = self.workflow.get('description', '')
        trigger = self.workflow.get('trigger', 'manual')
        
        md = f"""# {name}

{description}

## Activation

This skill is activated by: **{self._format_trigger(trigger)}**

## Workflow

"""
        # Add steps documentation
        for i, step in enumerate(self.workflow.get('steps', []), 1):
            if 'parallel' in step:
                md += f"### Parallel Execution\n"
                for pstep in step['parallel']:
                    md += self._format_step(pstep, level=4)
            else:
                md += self._format_step(step, level=3)
        
        # Add tools section
        tools = self.workflow.get('tools', {})
        if tools:
            md += "\n## Required Tools\n\n"
            for tool_name, tool_config in tools.items():
                md += f"- **{tool_name}**: {tool_config.get('type', 'unknown')}\n"
        
        # Add env vars section
        env_vars = self.workflow.get('env', {})
        if env_vars:
            md += "\n## Environment Variables\n\n"
            for var_name, var_value in env_vars.items():
                required = " (required)" if var_value == "required" else ""
                md += f"- `{var_name}`{required}\n"
        
        return md
    
    def _format_trigger(self, trigger: Any) -> str:
        """Format trigger for documentation"""
        if isinstance(trigger, str):
            if trigger.startswith('cron'):
                return f"Cron schedule: {trigger}"
            return trigger
        elif isinstance(trigger, dict):
            return f"{trigger.get('type', 'unknown')}: {trigger}"
        return "manual"
    
    def _format_step(self, step: Dict[str, Any], level: int = 3) -> str:
        """Format a step for documentation"""
        heading = "#" * level
        step_id = step.get('id', 'unnamed')
        intent = step.get('intent', 'No description')
        tools = step.get('tools', [])
        when = step.get('when')
        output = step.get('output')
        
        md = f"{heading} {step_id}\n\n"
        md += f"**Intent:** {intent}\n\n"
        
        if when:
            md += f"**Condition:** `{when}`\n\n"
        if tools:
            md += f"**Tools:** {', '.join(tools)}\n\n"
        if output:
            md += f"**Output:** `{output}`\n\n"
        
        return md
    
    def _generate_skill_json(self) -> Dict[str, Any]:
        """Generate skill.json metadata"""
        return {
            "name": self.workflow.get('name', 'unnamed'),
            "version": "1.0.0",
            "description": self.workflow.get('description', ''),
            "trigger": self.workflow.get('trigger', 'manual'),
            "runtime": "openclaw",
            "source_format": "map",
            "map_version": self.workflow.get('version', '1.0')
        }
    
    def _generate_agents_md(self) -> str:
        """Generate AGENTS.md with workflow context"""
        name = self.workflow.get('name', 'unnamed')
        
        md = f"""# {name} - Agent Context

This file provides context for the {name} workflow.

## Workflow Steps

"""
        for step in self.workflow.get('steps', []):
            if 'parallel' in step:
                md += "**Parallel Steps:**\n"
                for pstep in step['parallel']:
                    md += f"- {pstep.get('id')}: {pstep.get('intent', '')}\n"
            else:
                md += f"- **{step.get('id')}**: {step.get('intent', '')}\n"
        
        md += "\n## Variable Reference\n\n"
        md += "Use these variables in your responses:\n"
        md += "- `{env.VAR_NAME}` - Environment variables\n"
        md += "- `{input.param}` - Input parameters\n"
        md += "- `{step_id}` - Output from previous steps\n"
        
        return md


def compile_to_openclaw(map_path: str, output_dir: str) -> None:
    """Compile MAP workflow to OpenClaw skill"""
    with open(map_path) as f:
        workflow = yaml.safe_load(f)
    
    compiler = OpenClawCompiler(workflow)
    compiler.compile(output_dir)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python map_to_openclaw.py <workflow.map.yaml> <output_dir>")
        sys.exit(1)
    
    compile_to_openclaw(sys.argv[1], sys.argv[2])
