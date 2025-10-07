import json
import globalenv

# Parse the config file into usable variables
def parse_config(config_path):
    
    try:
        config = open(config_path, 'r')
        config = json.load(config)
        
        globalenv.client_cert = config['CertPath']
        globalenv.client_key = config['KeyPath']
        globalenv.seed_path = config['TOTPPath']
        globalenv.server_url = config['ServerURL']
        globalenv.esv_version = config['EsvVersion']

        if globalenv.verboseMode:
            print("Config file successfully parsed")
        
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse configuration file '{config_path}': {e}")
        exit(1)
    except KeyError as e:
        print(f"Error: Missing key '{e}' in configuration file '{config_path}'.")
        exit(1)
    except Exception as e:
        print(f"Error: An error occurred while parsing configuration file '{config_path}': {e}")
        exit(1)    

#Parse the run file into usable variables
def parse_run(run_path):

    try:
        run_file = open(run_path, 'r')
        globalenv.run_data = json.load(run_file)

    except FileNotFoundError:
        print(f"Error: Run file '{run_path}' not found")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse run file '{run_path}': {e}")
        exit(1)
    except Exception as e:
        print(f"Error: An error occurred while parsing run file '{run_path}': {e}")
        exit(1)
    if not globalenv.run_data:
        print(f"Error: Nothing parsed from run file '{run_path}'")
        exit(1)
