import subprocess
import logging

# Setup logging to track script execution
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define a function to run each script
def run_script(script_name):
    try:
        logging.info(f"Running {script_name}...")
        # Run the script as a separate process
        result = subprocess.run(['python', script_name], capture_output=True, text=True, check=True)
        
        # Log and print output for monitoring
        logging.info(f"Completed {script_name} successfully.")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running {script_name}: {e.stderr}")
        return f"Error running {script_name}: {e.stderr}"

# Define the sequence in which to run scripts
def main():
    output = []
    # output.append(run_script('main.py'))
    output.append(run_script('OutCsv.py'))
    output.append(run_script('episode.py'))
    output.append(run_script('movieaction.py'))
    output.append(run_script('combination.py'))
    output.append(run_script('database.py'))
    
    logging.info("All scripts have completed.")
    return output
