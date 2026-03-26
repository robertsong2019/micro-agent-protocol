#!/usr/bin/env python3
"""
Tests for MAP Interpreter
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from map_interpreter import MAPInterpreter, VariableResolver
from compilers.map_to_openclaw import OpenClawCompiler
import yaml


class TestVariableResolver:
    """Tests for variable resolution"""
    
    def test_simple_variable(self):
        context = {"name": "test"}
        resolver = VariableResolver(context)
        assert resolver.resolve("{name}") == "test"
    
    def test_nested_variable(self):
        context = {"env": {"API_KEY": "secret"}}
        resolver = VariableResolver(context)
        assert resolver.resolve("{env.API_KEY}") == "secret"
    
    def test_dict_resolution(self):
        context = {"step1": {"result": "data"}}
        resolver = VariableResolver(context)
        result = resolver.resolve({"input": "{step1.result}"})
        assert result["input"] == "data"


class TestMAPInterpreter:
    """Tests for MAP interpreter"""
    
    def test_load_workflow(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                "version": "1.0",
                "name": "test-workflow",
                "steps": [
                    {"id": "step1", "intent": "Test step"}
                ]
            }, f)
            f.flush()
            
            interpreter = MAPInterpreter(f.name)
            assert interpreter.workflow["name"] == "test-workflow"
            
            os.unlink(f.name)
    
    def test_missing_version(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                "name": "test-workflow",
                "steps": []
            }, f)
            f.flush()
            
            with pytest.raises(ValueError, match="version"):
                MAPInterpreter(f.name)
            
            os.unlink(f.name)
    
    def test_missing_name(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                "version": "1.0",
                "steps": []
            }, f)
            f.flush()
            
            with pytest.raises(ValueError, match="name"):
                MAPInterpreter(f.name)
            
            os.unlink(f.name)
    
    def test_run_simple_workflow(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                "version": "1.0",
                "name": "simple-test",
                "steps": [
                    {"id": "step1", "intent": "Test intent"}
                ]
            }, f)
            f.flush()
            
            interpreter = MAPInterpreter(f.name)
            results = interpreter.run()
            
            assert "step1" in results
            assert results["step1"].success
            
            os.unlink(f.name)


class TestOpenClawCompiler:
    """Tests for OpenClaw compiler"""
    
    def test_generate_skill_md(self):
        workflow = {
            "version": "1.0",
            "name": "test-skill",
            "description": "Test skill",
            "steps": [
                {"id": "step1", "intent": "Do something"}
            ]
        }
        
        compiler = OpenClawCompiler(workflow)
        skill_md = compiler._generate_skill_md()
        
        assert "test-skill" in skill_md
        assert "step1" in skill_md
        assert "Do something" in skill_md
    
    def test_generate_skill_json(self):
        workflow = {
            "version": "1.0",
            "name": "test-skill",
            "description": "Test skill"
        }
        
        compiler = OpenClawCompiler(workflow)
        skill_json = compiler._generate_skill_json()
        
        assert skill_json["name"] == "test-skill"
        assert skill_json["version"] == "1.0.0"
        assert skill_json["runtime"] == "openclaw"


class TestExamples:
    """Test example workflows"""
    
    def test_validate_tech_news_digest(self):
        example_path = Path(__file__).parent.parent / "examples" / "tech-news-digest.map.yaml"
        if example_path.exists():
            interpreter = MAPInterpreter(str(example_path))
            assert interpreter.workflow["name"] == "tech-news-digest"
    
    def test_validate_code_review(self):
        example_path = Path(__file__).parent.parent / "examples" / "multi-agent-code-review.map.yaml"
        if example_path.exists():
            interpreter = MAPInterpreter(str(example_path))
            assert interpreter.workflow["name"] == "code-review-agents"
    
    def test_validate_iot_monitor(self):
        example_path = Path(__file__).parent.parent / "examples" / "iot-sensor-monitor.map.yaml"
        if example_path.exists():
            interpreter = MAPInterpreter(str(example_path))
            assert interpreter.workflow["name"] == "iot-sensor-monitor"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
