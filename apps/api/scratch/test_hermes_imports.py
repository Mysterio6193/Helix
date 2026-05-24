import sys

# Prepend the hermes path
HERMES_PATH = "/Users/mihirsachdev/Downloads/MARK FINAL/helix/packages/vendor/hermes-agent"
if HERMES_PATH not in sys.path:
    sys.path.insert(0, HERMES_PATH)

try:
    from tools.registry import registry
    
    # Let's check registering a dummy tool under 'helix'
    def dummy_handler(**kwargs):
        return "Dummy result"
        
    dummy_schema = {
        "name": "dummy_helix_tool",
        "description": "A dummy tool for Helix",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "A parameter"}
            },
            "required": ["param1"]
        }
    }
    
    registry.register(
        name="dummy_helix_tool",
        toolset="helix",
        schema=dummy_schema,
        handler=dummy_handler,
        is_async=False,
    )
except Exception:
    import traceback
    traceback.print_exc()
