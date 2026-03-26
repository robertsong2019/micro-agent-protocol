#!/usr/bin/env python3
"""
MAP Interpreter - Minimal implementation of Micro Agent Protocol
"""

import yaml
import json
import re
import os
import sys
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class StepResult:
    id: str
    output: Any
    success: bool
    error: Optional[str] = None


class VariableResolver:
    """Resolves {variable} references in strings"""
    
    def __init__(self, context: Dict[str, Any]):
        self.context = context
        
    def resolve(self, text: Any) -> Any:
        if isinstance(text, str):
            # Find all {variable} patterns
            pattern = r'\{([^}]+)\}'
            
            def replace(match):
                var_path = match.group(1)
                return str(self._get_value(var_path))
            
            return re.sub(pattern, replace, text)
        elif isinstance(text, dict):
            return {k: self.resolve(v) for k, v in text.items()}
        elif isinstance(text, list):
            return [self.resolve(item) for item in text]
        return text
    
    def _get_value(self, path: str) -> Any:
        """Navigate nested path like 'env.API_KEY' or 'step_id.field'"""
        parts = path.split('.')
        value = self.context
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
                
        return value


class MockLLM:
    """Mock LLM for demo purposes - in reality, this would call actual LLM"""
    
    def execute_intent(self, intent: str, context: Dict[str, Any], tools: List[str]) -> Any:
        """Execute natural language intent"""
        # In a real implementation, this would:
        # 1. Send intent + context to LLM
        # 2. LLM generates code or actions
        # 3. Execute those actions
        
        # Mock response based on intent keywords
        intent_lower = intent.lower()
        
        if "fetch" in intent_lower or "get" in intent_lower:
            return {"data": f"[Mock data for: {intent}]", "status": "success"}
        elif "summarize" in intent_lower or "summary" in intent_lower:
            return f"[Mock summary generated for: {intent}]"
        elif "send" in intent_lower or "post" in intent_lower:
            return {"sent": True, "message": f"[Sent: {intent}]"}
        else:
            return f"[Executed: {intent}]"


class ToolExecutor:
    """Executes tool actions"""
    
    def __init__(self, tools_config: Dict[str, Any]):
        self.tools = tools_config
        
    def execute(self, tool_name: str, action: str, params: Dict[str, Any]) -> Any:
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not defined")
            
        tool_type = tool.get('type')
        
        if tool_type == 'http':
            return self._execute_http(tool, action, params)
        elif tool_type == 'webhook':
            return self._execute_webhook(tool, params)
        elif tool_type == 'shell':
            return self._execute_shell(tool, params)
        else:
            return {"status": "mock", "tool": tool_name, "action": action}
    
    def _execute_http(self, tool: Dict, action: str, params: Dict) -> Any:
        """Execute HTTP tool (mock implementation)"""
        return {"mock_http": True, "base_url": tool.get('base_url')}
    
    def _execute_webhook(self, tool: Dict, params: Dict) -> Any:
        """Execute webhook (mock implementation)"""
        return {"mock_webhook": True, "url": tool.get('url')}
    
    def _execute_shell(self, tool: Dict, params: Dict) -> Any:
        """Execute shell command (mock implementation)"""
        return {"mock_shell": True, "allowed": tool.get('allowed_commands')}


class MAPInterpreter:
    """Main interpreter for MAP workflows"""
    
    def __init__(self, workflow_path: str):
        self.workflow = self._load_workflow(workflow_path)
        self.context: Dict[str, Any] = {}
        self.llm = MockLLM()
        self.tool_executor = None
        
    def _load_workflow(self, path: str) -> Dict[str, Any]:
        """Load and validate MAP workflow"""
        with open(path) as f:
            workflow = yaml.safe_load(f)
        
        # Validate required fields
        if workflow.get('version') != '1.0':
            raise ValueError("Only MAP version 1.0 is supported")
        if not workflow.get('name'):
            raise ValueError("Workflow 'name' is required")
        if not workflow.get('steps'):
            raise ValueError("Workflow 'steps' are required")
            
        return workflow
    
    def run(self, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the workflow"""
        # Initialize context
        self.context = {
            'env': self._resolve_env(),
            'input': inputs or {},
            'steps': {}
        }
        
        # Initialize tools
        self.tool_executor = ToolExecutor(self.workflow.get('tools', {}))
        
        # Execute steps
        for step in self.workflow['steps']:
            self._execute_step(step)
        
        return self.context['steps']
    
    def _resolve_env(self) -> Dict[str, str]:
        """Resolve environment variables"""
        env_spec = self.workflow.get('env', {})
        resolved = {}
        
        for key, value in env_spec.items():
            if value == 'required':
                val = os.environ.get(key)
                if not val:
                    raise ValueError(f"Required env var {key} not set")
                resolved[key] = val
            else:
                resolved[key] = os.environ.get(key, value)
                
        return resolved
    
    def _execute_step(self, step: Dict[str, Any]) -> None:
        """Execute a single step"""
        # Check for parallel execution
        if 'parallel' in step:
            for parallel_step in step['parallel']:
                self._execute_step(parallel_step)
            return
        
        step_id = step['id']
        resolver = VariableResolver(self.context)
        
        # Check condition
        if 'when' in step:
            condition = resolver.resolve(step['when'])
            # Simple eval for conditions (in production, use safe eval)
            if not self._eval_condition(condition):
                self.context['steps'][step_id] = StepResult(
                    id=step_id,
                    output=None,
                    success=True,
                    error="Condition not met"
                )
                return
        
        # Resolve inputs
        intent = resolver.resolve(step.get('intent', ''))
        step_input = resolver.resolve(step.get('input', {}))
        step_tools = step.get('tools', [])
        
        # Execute intent
        try:
            output = self.llm.execute_intent(intent, step_input, step_tools)
            
            # Store result
            self.context['steps'][step_id] = StepResult(
                id=step_id,
                output=output,
                success=True
            )
            
            # Also store in context for variable references
            output_var = step.get('output')
            if output_var:
                self.context[output_var] = output
                
        except Exception as e:
            self.context['steps'][step_id] = StepResult(
                id=step_id,
                output=None,
                success=False,
                error=str(e)
            )
    
    def _eval_condition(self, condition: str) -> bool:
        """Safely evaluate condition (mock implementation)"""
        # In production, use a safe expression evaluator
        # For demo, return True
        return True


def main():
    if len(sys.argv) < 2:
        print("Usage: map run <workflow.yaml>")
        sys.exit(1)
    
    workflow_path = sys.argv[1]
    
    # Parse additional arguments as inputs
    inputs = {}
    if len(sys.argv) > 2:
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                inputs[key] = value
    
    interpreter = MAPInterpreter(workflow_path)
    results = interpreter.run(inputs)
    
    # Pretty print results
    print("\n=== Workflow Results ===\n")
    for step_id, result in results.items():
        print(f"Step: {step_id}")
        print(f"  Success: {result.success}")
        if result.output:
            print(f"  Output: {json.dumps(result.output, indent=4)}")
        if result.error:
            print(f"  Error: {result.error}")
        print()


if __name__ == '__main__':
    main()
