import json
import wandb
import os

def read_json(file_path):
    """Read and parse a JSON file."""
    try:
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
            return data
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    return None

def process_json(file_path):
    """Process a single JSON file and log results to wandb."""
    results_json = read_json(file_path)
    if results_json is None:
        return

    # Initialize a wandb Table for logging all test cases
    table = wandb.Table(columns=["Input", "Output", "Answer Relevancy Score", "Answer Relevancy Reason","Contextual Recall","Contextual Recall Reason", "Contextual Precision", "Contextual Precision Reason" , "Retrieved Contexts", "Ground Truth Output"])

    # Extract test case data
    test_cases = list(results_json["test_cases_lookup_map"].items())
    metrics_aggregated = {}
    metrics_success_counts = {}
    for key, value in test_cases:
        metrics_data = value["cached_metrics_data"]
        real_key = json.loads(key)

        # Extract input, retrieval context, actual output, and expected output
        input_text = real_key["input"]
        retrieval_context = real_key["retrieval_context"]
        actual_output = real_key["actual_output"]
        expected_output = real_key["expected_output"]

        # Consolidate metrics into a dictionary
        metrics_score = {metric["metric_data"]["name"]: metric["metric_data"]["score"] for metric in metrics_data}
        metrics_reason = {metric["metric_data"]["name"]: metric["metric_data"]["reason"] for metric in metrics_data}

        for metric in metrics_data:
            metric_name = metric["metric_data"]["name"]
            metric_score = metric["metric_data"]["score"]
            success = metric["metric_data"].get("success", False)  # Get success for the metric
    
            if metric_name not in metrics_aggregated:
                metrics_aggregated[metric_name] = []
                metrics_success_counts[metric_name] = 0
    
            metrics_aggregated[metric_name].append(metric_score)
            if success:
                metrics_success_counts[metric_name] += 1
        
 

        # Add the row to the table
        keys_of_metrics = ["Answer Relevancy", "Contextual Recall", "Contextual Precision"]
        for metric in keys_of_metrics:
            if metric not in metrics_score.keys():
                metrics_score[metric] = None
                metrics_reason[metric] = None

        table.add_data(input_text, actual_output, metrics_score["Answer Relevancy"],metrics_reason["Answer Relevancy"],metrics_score["Contextual Recall"],metrics_reason["Contextual Recall"] ,metrics_score["Contextual Precision"],metrics_reason["Contextual Precision"],retrieval_context, expected_output)

    total_averages = {}
    metrics_success_rates = {}
    for metric_name, scores in metrics_aggregated.items():
        total_averages[metric_name] = sum(scores) / len(scores)
        metrics_success_rates[metric_name] = (metrics_success_counts[metric_name] / len(scores)) * 100

    for metric_name in total_averages:
        print(f"{metric_name}:")
        print(f"  Average Score: {total_averages[metric_name]:.2f}")
        print(f"  Success Rate: {metrics_success_rates[metric_name]:.2f}%")
    
        # Log each metric separately
        wandb.log({
            f"{metric_name} Average Score": total_averages[metric_name],
            f"{metric_name} Success Rate": metrics_success_rates[metric_name]
        })

    # Log the table to wandb
    wandb.log({"Test Case Table": table})
    mean_score = sum(total_averages.values()) / len(total_averages) if total_averages else 0
    wandb.log({"Mean Score": mean_score})

# Define Sweep configuration
sweep_config = {
    "method": "grid",  # Use grid search to iterate over all files
    "parameters": {

        "model_name": {
            "values": ["gemma-2-9b-it-Q4_K_M"]  # Extracted manually
        },
        "embedding_model_name": {
            "values": ["gte-tiny","all-MiniLM-L6-v2"]  # Extracted manually
        },
        
        "topk": {
            "values": [5,10]  # Extracted manually
        },
        "prompt_template_number": {
            "values": [1,0]  # Extracted manually
        }
    }
}
# Initialize the Sweep
sweep_id = wandb.sweep(sweep=sweep_config, project="Kizir-AI-Parameter-Tuning-2")

# Agent function to process JSON files
def sweep_agent():
    # Access the JSON file path from the wandb configuration
    with wandb.init(project="test_case_metrics_logging2"):
        model_name = wandb.config["model_name"]
        topk = str(wandb.config["topk"])
        embedding_model_name = wandb.config["embedding_model_name"]
        prompt_template_number = str(wandb.config["prompt_template_number"])
        file_path = f"{model_name}_{embedding_model_name}_{topk}_{prompt_template_number}_evaluation_results_deepeval_cache.json"
        process_json(file_path)

# Run the Sweep Agent
wandb.agent(sweep_id, function=sweep_agent)
