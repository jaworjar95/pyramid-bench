#!/usr/bin/env python3
"""
Pyramid Puzzle LLM Benchmark

Evaluates LLM performance on spatial reasoning and pathfinding through
a pyramid puzzle game.
"""

import argparse
import os
import sys
import yaml
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

from game_validator import validate_puzzle_solution
from openrouter_client import create_client
from logger import create_logger


class BenchmarkRunner:
    """Main benchmark runner class."""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            print("Error: OPENROUTER_API_KEY not found in environment variables.")
            print("Please copy .env.example to .env and configure your API key.")
            sys.exit(1)
        
        # Configuration
        self.models = self._parse_models()
        self.temperature = float(os.getenv("GLOBAL_TEMPERATURE", 0.7))
        self.max_tokens = int(os.getenv("GLOBAL_MAX_TOKENS", 2000))
        self.site_url = os.getenv("SITE_URL")
        self.site_name = os.getenv("SITE_NAME")
        
        # Initialize components
        self.client = create_client(self.api_key, self.site_url, self.site_name)
        self.logger = create_logger()
        
        # Load specifications
        self.rules_content = self._load_file("tasks/specs/Rules.md")
        self.output_notation_content = self._load_file("tasks/specs/Output_Notations.md")
        self.initial_prompt_content = self._load_file("tasks/specs/Initial_Prompt.md")
    
    def _parse_models(self) -> List[str]:
        """Parse models from environment variable."""
        models_str = os.getenv("MODELS", "")
        if not models_str:
            print("Error: MODELS not configured in environment variables.")
            sys.exit(1)
        return [model.strip() for model in models_str.split(",")]
    
    def _load_file(self, filepath: str) -> str:
        """Load content from file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Error: Required file not found: {filepath}")
            sys.exit(1)
    
    def _load_scenario(self, scenario_path: str) -> Dict[str, Any]:
        """Load scenario configuration from YAML file."""
        try:
            with open(scenario_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Error: Scenario file not found: {scenario_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing scenario YAML: {e}")
            sys.exit(1)
    
    def _build_scenario_prompt(self, scenario_config: Dict[str, Any]) -> str:
        """Build scenario-specific prompt content."""
        scenario_data = list(scenario_config.values())[0]  # Get first scenario
        
        prompt_parts = []
        
        # Configuration section
        config = scenario_data.get("configuration", {})
        
        prompt_parts.append("## SCENARIO CONFIGURATION\\n")
        
        # Blocked tiles
        blocked = config.get("blocked", [])
        if blocked:
            blocked_tiles = [tile["tile"] for tile in blocked]
            prompt_parts.append(f"**Blocked Tiles:** {', '.join(blocked_tiles)}\\n")
        
        # Collectibles
        collectibles = config.get("collectibles", [])
        if collectibles:
            prompt_parts.append("**Items Available:**\\n")
            for item in collectibles:
                prompt_parts.append(f"- {item['type'].title()}: Located at {item['location']}\\n")
        
        # Objective
        objective = config.get("objective", {})
        goal_tile = objective.get("goal_tile", "A1")
        requires = objective.get("requires", [])
        prompt_parts.append(f"**Objective:** Reach {goal_tile}")
        if requires:
            prompt_parts.append(f" (requires: {', '.join(requires)})")
        prompt_parts.append("\\n\\n")
        
        return "".join(prompt_parts)
    
    def _build_full_prompt(self, scenario_config: Dict[str, Any], hint: str = None) -> str:
        """Build the complete prompt for the model."""
        prompt_parts = [
            self.rules_content,
            "\\n---\\n\\n",
            self._build_scenario_prompt(scenario_config),
            self.output_notation_content,
            "\\n\\n",
            self.initial_prompt_content
        ]
        
        if hint:
            prompt_parts.extend(["\\n\\n**HINT:** ", hint])
        
        return "".join(prompt_parts)
    
    def _evaluate_response(self, response_json: Dict[str, Any], scenario_config: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate model response against game rules."""
        if not response_json:
            return {
                "is_valid_format": False,
                "format_error": "Could not parse JSON response",
                "is_valid_path": False,
                "path_error": "No valid response to evaluate",
                "total_mp": 0,
                "is_optimal": False
            }
        
        # Validate format
        format_valid, format_error = self.client.validate_response_format(response_json)
        if not format_valid:
            return {
                "is_valid_format": False,
                "format_error": format_error,
                "is_valid_path": False,
                "path_error": "Invalid format prevents path validation",
                "total_mp": 0,
                "is_optimal": False
            }
        
        # Validate path using game rules
        path = response_json["path"]
        scenario_data = list(scenario_config.values())[0]
        config = scenario_data.get("configuration", {})
        
        validation_result = validate_puzzle_solution(path, config)
        
        return {
            "is_valid_format": True,
            "format_error": "",
            "is_valid_path": validation_result["is_valid"],
            "path_error": validation_result["message"] if not validation_result["is_valid"] else "",
            "total_mp": validation_result["total_mp"],
            "is_optimal": validation_result["is_optimal"],
            "optimal_mp": validation_result.get("optimal_mp", 0)
        }
    
    def _run_scenario_for_model(self, model: str, scenario_path: str) -> Dict[str, Any]:
        """Run a single scenario evaluation for a specific model."""
        print(f"\\nEvaluating {model} on {os.path.basename(scenario_path)}...")
        
        scenario_config = self._load_scenario(scenario_path)
        scenario_data = list(scenario_config.values())[0]
        scenario_id = list(scenario_config.keys())[0]
        
        interactions = []
        interaction_count = 0
        
        # Get hints from scenario
        solution_info = scenario_data.get("solution", {})
        hints = [
            solution_info.get("hint_1"),
            solution_info.get("hint_2"), 
            solution_info.get("hint_3")
        ]
        hints = [h for h in hints if h]  # Remove None values
        
        # Initial attempt
        interaction_count += 1
        prompt = self._build_full_prompt(scenario_config)
        
        # Try up to 3 retries for invalid responses
        for retry in range(4):  # 0 = initial, 1-3 = retries
            interaction_type = "initial" if retry == 0 else f"retry_{retry}"
            
            print(f"  Attempt {retry + 1}...")
            
            # Send to model
            response_json, raw_response, token_usage, response_time = self.client.send_message(
                model, prompt, self.temperature, self.max_tokens
            )
            
            # Evaluate response
            evaluation = self._evaluate_response(response_json, scenario_config)
            
            # Prepare interaction data
            interaction_data = {
                "interaction_number": interaction_count,
                "interaction_type": interaction_type,
                "prompt": prompt,
                "raw_response": raw_response,
                "parsed_json": str(response_json) if response_json else "",
                "path": response_json.get("path", "") if response_json else "",
                "analysis": response_json.get("analysis", "") if response_json else "",
                "success": evaluation["is_valid_path"] and evaluation["is_optimal"],
                **evaluation,
                **token_usage,
                "response_time": response_time
            }
            
            interactions.append(interaction_data)
            self.logger.log_interaction(model, scenario_id, interaction_data)
            
            # Check if we have a valid response
            if evaluation["is_valid_format"] and evaluation["is_valid_path"]:
                if evaluation["is_optimal"]:
                    print(f"  ✓ Found optimal solution! ({evaluation['total_mp']} MP)")
                    final_result = {"success": True, "is_optimal": True, "total_mp": evaluation["total_mp"]}
                    self.logger.create_markdown_report(model, scenario_id, interactions, final_result, scenario_data)
                    return final_result
                else:
                    print(f"  → Valid but not optimal ({evaluation['total_mp']} MP, optimal: {evaluation.get('optimal_mp', 'unknown')})")
                    break  # Move to hints
            else:
                # Give specific feedback for retry
                if not evaluation["is_valid_format"]:
                    error_msg = f"Invalid response format: {evaluation['format_error']}"
                else:
                    error_msg = f"Invalid path: {evaluation['path_error']}"
                
                print(f"  ✗ {error_msg}")
                
                if retry < 3:  # Don't modify prompt on last retry
                    prompt += f"\\n\\nYour previous response had an error: {error_msg}\\nPlease provide a corrected response in the exact JSON format specified."
        
        # If we get here, either we have a valid but non-optimal solution, or all retries failed
        last_interaction = interactions[-1]
        
        if not last_interaction["is_valid_path"]:
            print("  ✗ Failed to provide valid solution after retries")
            final_result = {"success": False, "is_optimal": False}
            self.logger.create_markdown_report(model, scenario_id, interactions, final_result, scenario_data)
            return final_result
        
        # Try hints for non-optimal but valid solutions
        for i, hint in enumerate(hints):
            interaction_count += 1
            hint_type = f"hint_{i+1}"
            
            print(f"  Trying {hint_type}...")
            
            hint_prompt = self._build_full_prompt(scenario_config, hint)
            
            response_json, raw_response, token_usage, response_time = self.client.send_message(
                model, hint_prompt, self.temperature, self.max_tokens
            )
            
            evaluation = self._evaluate_response(response_json, scenario_config)
            
            interaction_data = {
                "interaction_number": interaction_count,
                "interaction_type": hint_type,
                "prompt": hint_prompt,
                "raw_response": raw_response,
                "parsed_json": str(response_json) if response_json else "",
                "path": response_json.get("path", "") if response_json else "",
                "analysis": response_json.get("analysis", "") if response_json else "",
                "success": evaluation["is_valid_path"] and evaluation["is_optimal"],
                **evaluation,
                **token_usage,
                "response_time": response_time
            }
            
            interactions.append(interaction_data)
            self.logger.log_interaction(model, scenario_id, interaction_data)
            
            if evaluation["is_valid_path"] and evaluation["is_optimal"]:
                print(f"  ✓ Found optimal solution with {hint_type}! ({evaluation['total_mp']} MP)")
                final_result = {"success": True, "is_optimal": True, "total_mp": evaluation["total_mp"]}
                self.logger.create_markdown_report(model, scenario_id, interactions, final_result, scenario_data)
                return final_result
            elif evaluation["is_valid_path"]:
                print(f"  → Still not optimal with {hint_type} ({evaluation['total_mp']} MP)")
            else:
                print(f"  ✗ Invalid response to {hint_type}")
        
        # Final result
        best_interaction = max((i for i in interactions if i["is_valid_path"]), 
                              key=lambda x: x.get("total_mp", float('inf')), default=None)
        
        if best_interaction:
            final_result = {"success": True, "is_optimal": False, "total_mp": best_interaction["total_mp"]}
            print(f"  → Final result: Valid solution found ({best_interaction['total_mp']} MP) but not optimal")
        else:
            final_result = {"success": False, "is_optimal": False}
            print("  ✗ No valid solution found")
        
        self.logger.create_markdown_report(model, scenario_id, interactions, final_result, scenario_data)
        return final_result
    
    def run_benchmark(self, scenarios: List[str], models: List[str]) -> None:
        """Run the complete benchmark."""
        print(f"Starting benchmark with {len(models)} models and {len(scenarios)} scenarios...")
        print(f"Models: {', '.join(models)}")
        print(f"Scenarios: {', '.join([os.path.basename(s) for s in scenarios])}")
        
        total_evaluations = len(models) * len(scenarios)
        current_evaluation = 0
        
        for model in models:
            for scenario_path in scenarios:
                current_evaluation += 1
                print(f"\\n[{current_evaluation}/{total_evaluations}]", end="")
                
                try:
                    self._run_scenario_for_model(model, scenario_path)
                except Exception as e:
                    print(f"\\nError evaluating {model} on {os.path.basename(scenario_path)}: {e}")
        
        print(f"\\n\\nBenchmark complete! Results saved in 'evals/' directory.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Pyramid Puzzle LLM Benchmark")
    parser.add_argument("--scenarios", default="all", 
                       help="Scenarios to run (comma-separated list or 'all')")
    parser.add_argument("--models", default="all",
                       help="Models to evaluate (comma-separated list or 'all')")
    
    args = parser.parse_args()
    
    # Initialize benchmark runner
    runner = BenchmarkRunner()
    
    # Parse scenarios
    if args.scenarios == "all":
        import glob
        scenario_files = glob.glob("tasks/scenarios/*.yaml")
        if not scenario_files:
            print("Error: No scenario files found in tasks/scenarios/")
            sys.exit(1)
    else:
        scenario_nums = [s.strip() for s in args.scenarios.split(",")]
        scenario_files = []
        for num in scenario_nums:
            path = f"tasks/scenarios/scenario_{num}.yaml"
            if os.path.exists(path):
                scenario_files.append(path)
            else:
                print(f"Warning: Scenario file not found: {path}")
    
    # Parse models
    if args.models == "all":
        models = runner.models
    else:
        requested_models = [m.strip() for m in args.models.split(",")]
        models = [m for m in requested_models if m in runner.models]
        if len(models) != len(requested_models):
            missing = set(requested_models) - set(models)
            print(f"Warning: Some requested models not found in config: {missing}")
    
    if not scenario_files:
        print("Error: No valid scenario files to process")
        sys.exit(1)
    
    if not models:
        print("Error: No valid models to evaluate")
        sys.exit(1)
    
    # Run benchmark
    runner.run_benchmark(scenario_files, models)


if __name__ == "__main__":
    main()