"""
Reproduce the analysis data.
  python run_all.py     # make_data -> analyze (writes the small aggregates)
Then:  streamlit run app/streamlit_app.py
"""
import subprocess, sys
for name, cmd in [("Generate experiment", ["python", "src/make_data.py"]),
                  ("Aggregate", ["python", "src/analyze.py"])]:
    print(f"\n=== {name} ===")
    if subprocess.run(cmd).returncode != 0:
        sys.exit(f"Step failed: {name}")
print("\nDone. Run:  streamlit run app/streamlit_app.py")
