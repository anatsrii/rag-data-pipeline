from src.mcp_tools import SourceTools
tools = SourceTools()
print("All Sources:")
for s in tools.list_sources():
    print(f"  - {s['name']}: {s['urls_count']} URLs ({s['category']})")
