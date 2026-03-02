from src.mcp_tools import SourceTools
tools = SourceTools()
sources = tools.list_sources()
for s in sources:
    print(f"- {s['name']} ({s['category']}): {s['raw_files']} files, {s['processed_files']} processed")
