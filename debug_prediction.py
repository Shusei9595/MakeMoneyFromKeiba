import pandas as pd
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path.cwd()))

from src.orchestrator.agent_manager import AgentManager

# Load data
df = pd.read_csv('data/live_20260107_urawa11r.csv.predict')

# Init AgentManager
am = AgentManager(model_dir='models')
print(f"Loaded agents: {am.get_loaded_agent_names()}")

# Try one prediction
agent = am.agents['past_performance_agent']
try:
    scores = agent.predict(df)
    print(f"Prediction success! Scores: {scores[:3]}")
except Exception as e:
    print(f"Prediction failed for {agent.name}: {e}")
    import traceback
    traceback.print_exc()
