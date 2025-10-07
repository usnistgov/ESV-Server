# Read from command line
global verboseMode, run_path, run_json, record_90B_stats, stats_90B_path
verboseMode = False
run_path = ""
run_data = {}
record_90B_stats = False
stats_90B_path = ""

# Read from config file
global seed_path, server_url, esv_version, client_cert, client_key
seed_path = ""
server_url = ""
esv_version = ""
client_cert = ""
client_key = ""

# Used in operation
global jwt
jwt = ""