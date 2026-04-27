import sys
sys.path.insert(0, '.')

try:
    from pentest_agent.tui import app
    print("✅ TUI imports successfully")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
