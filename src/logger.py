"""
Logger for benchmark results - handles CSV and Markdown output.
"""

import csv
import os
from datetime import datetime
from typing import Dict, Any, List


class BenchmarkLogger:
    """Logger for benchmark interactions and results."""
    
    def __init__(self, base_dir: str = "evals"):
        self.base_dir = base_dir
        self.csv_dir = os.path.join(base_dir, "csv")
        self.markdown_dir = os.path.join(base_dir, "markdown")
        
        # Ensure directories exist
        os.makedirs(self.csv_dir, exist_ok=True)
        os.makedirs(self.markdown_dir, exist_ok=True)
        
        # CSV fieldnames
        self.csv_fieldnames = [
            "timestamp",
            "model_name",
            "scenario_id",
            "interaction_number",
            "interaction_type",  # initial, hint_1, hint_2, hint_3, retry
            "prompt",
            "raw_response",
            "parsed_json",
            "path",
            "analysis",
            "is_valid_format",
            "format_error",
            "is_valid_path",
            "path_error",
            "total_mp",
            "optimal_mp",
            "is_optimal",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "response_time",
            "success"
        ]
    
    def generate_filename(self, model_name: str, scenario_id: str) -> str:
        """Generate filename for this model/scenario combination."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_model = model_name.replace("/", "_").replace(":", "_")
        return f"{clean_model}_scenario_{scenario_id}_{timestamp}"
    
    def log_interaction(self, model_name: str, scenario_id: str, interaction_data: Dict[str, Any]):
        """Log a single interaction to CSV."""
        filename = self.generate_filename(model_name, scenario_id)
        csv_path = os.path.join(self.csv_dir, f"{filename}.csv")
        
        # Check if file exists to determine if we need headers
        file_exists = os.path.exists(csv_path)
        
        # Ensure all required fields exist
        row_data = {field: interaction_data.get(field, "") for field in self.csv_fieldnames}
        row_data["timestamp"] = datetime.now().isoformat()
        row_data["model_name"] = model_name
        row_data["scenario_id"] = scenario_id
        
        with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.csv_fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(row_data)
    
    def create_markdown_report(self, model_name: str, scenario_id: str, 
                             interactions: List[Dict[str, Any]], 
                             final_result: Dict[str, Any],
                             scenario_config: Dict[str, Any]):
        """Create a comprehensive markdown report for the scenario evaluation."""
        filename = self.generate_filename(model_name, scenario_id)
        md_path = os.path.join(self.markdown_dir, f"{filename}.md")
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# Benchmark Report: {model_name} - Scenario {scenario_id}\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            
            # Summary
            f.write("## Summary\n\n")
            f.write(f"- **Model:** {model_name}\n")
            f.write(f"- **Scenario:** {scenario_id}\n")
            f.write(f"- **Total Interactions:** {len(interactions)}\n")
            f.write(f"- **Final Result:** {'SUCCESS' if final_result.get('success', False) else 'FAILED'}\n")
            f.write(f"- **Optimal Solution Found:** {'YES' if final_result.get('is_optimal', False) else 'NO'}\n")
            
            if final_result.get('total_mp'):
                f.write(f"- **Final MP:** {final_result['total_mp']}\n")
            if scenario_config.get('solution', {}).get('optimal_mp'):
                f.write(f"- **Optimal MP:** {scenario_config['solution']['optimal_mp']}\n")
            
            # Token usage summary
            total_prompt_tokens = sum(i.get('prompt_tokens', 0) for i in interactions)
            total_completion_tokens = sum(i.get('completion_tokens', 0) for i in interactions)
            total_tokens = sum(i.get('total_tokens', 0) for i in interactions)
            
            f.write(f"- **Total Tokens Used:** {total_tokens} (Prompt: {total_prompt_tokens}, Completion: {total_completion_tokens})\n")
            f.write(f"- **Total Response Time:** {sum(i.get('response_time', 0) for i in interactions):.2f} seconds\n\n")
            
            # Scenario configuration
            f.write("## Scenario Configuration\n\n")
            f.write("### Blocked Tiles\n")
            blocked = scenario_config.get('blocked', [])
            if blocked:
                f.write(", ".join([tile['tile'] for tile in blocked]) + "\n\n")
            else:
                f.write("None\n\n")
            
            f.write("### Collectibles\n")
            collectibles = scenario_config.get('collectibles', [])
            for item in collectibles:
                f.write(f"- **{item['type'].title()}:** {item['location']}\n")
            f.write("\n")
            
            # Detailed interactions
            f.write("## Interaction Log\n\n")
            
            for i, interaction in enumerate(interactions, 1):
                f.write(f"### Interaction {i}: {interaction.get('interaction_type', 'unknown').title()}\n\n")
                
                # Prompt (truncated for readability)
                prompt = interaction.get('prompt', '')
                if len(prompt) > 1000:
                    prompt = prompt[:1000] + "...[truncated]"
                f.write(f"**Prompt:** \n```\n{prompt}\n```\n\n")
                
                # Response
                f.write(f"**Raw Response:** \n```\n{interaction.get('raw_response', '')}\n```\n\n")
                
                # Parsed data
                if interaction.get('parsed_json'):
                    f.write(f"**Path:** `{interaction.get('path', 'N/A')}`\n\n")
                    f.write(f"**Analysis:** {interaction.get('analysis', 'N/A')}\n\n")
                
                # Validation results
                f.write("**Validation Results:**\n")
                f.write(f"- Format Valid: {'✓' if interaction.get('is_valid_format', False) else '✗'}\n")
                if not interaction.get('is_valid_format', False):
                    f.write(f"  - Error: {interaction.get('format_error', 'N/A')}\n")
                
                f.write(f"- Path Valid: {'✓' if interaction.get('is_valid_path', False) else '✗'}\n")
                if not interaction.get('is_valid_path', False):
                    f.write(f"  - Error: {interaction.get('path_error', 'N/A')}\n")
                
                if interaction.get('total_mp'):
                    f.write(f"- MP Count: {interaction.get('total_mp')}\n")
                    f.write(f"- Optimal: {'✓' if interaction.get('is_optimal', False) else '✗'}\n")
                
                # Performance metrics
                f.write(f"- Tokens: {interaction.get('total_tokens', 0)} (P: {interaction.get('prompt_tokens', 0)}, C: {interaction.get('completion_tokens', 0)})\n")
                f.write(f"- Response Time: {interaction.get('response_time', 0):.2f}s\n\n")
                
                f.write("---\n\n")
            
            # Final assessment
            f.write("## Final Assessment\n\n")
            if final_result.get('success', False):
                if final_result.get('is_optimal', False):
                    f.write("🎉 **SUCCESS:** Model found the optimal solution!\n\n")
                else:
                    f.write("✅ **PARTIAL SUCCESS:** Model found a valid solution, but not optimal.\n\n")
            else:
                f.write("❌ **FAILURE:** Model failed to find a valid solution.\n\n")
            
            # Hints used
            hint_types = [i.get('interaction_type', '') for i in interactions]
            hints_used = [h for h in hint_types if h.startswith('hint_')]
            if hints_used:
                f.write(f"**Hints Used:** {', '.join(hints_used)}\n\n")
            
            f.write(f"**Report Generated:** {datetime.now().isoformat()}\n")


def create_logger(base_dir: str = "evals") -> BenchmarkLogger:
    """Factory function to create benchmark logger."""
    return BenchmarkLogger(base_dir)