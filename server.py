import sys, json

TOOLS = [{
    "name": "process_json",
    "description": "JSON处理工具 - 格式化、验证、转换、查询JSON数据",
    "inputSchema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["format", "validate", "flatten", "unflatten", "query", "convert_csv", "convert_yaml"],
                "description": "操作类型"
            },
            "data": {"type": "string", "description": "JSON字符串"},
            "query_path": {"type": "string", "description": "JSONPath查询路径，如 $.store.book[0].title"}
        },
        "required": ["action", "data"]
    }
}]

async def handle_mcp(body):
    method = body.get("method", "")
    params = body.get("params", {})
    rid = body.get("id")
    
    if method == "initialize":
        return {"jsonrpc":"2.0","id":rid,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"JSON Processor","version":"1.0.0"}}}
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None
    if method == "tools/list":
        return {"jsonrpc":"2.0","id":rid,"result":{"tools":TOOLS}}
    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})
        result = process(args.get("action",""), args.get("data",""), args.get("query_path",""))
        return {"jsonrpc":"2.0","id":rid,"result":{"content":[{"type":"text","text":json.dumps(result,ensure_ascii=False)}],"isError":not result.get("success")}}
    return {"jsonrpc":"2.0","id":rid,"error":{"code":-32601,"message":f"Unknown: {method}"}}

def process(action, data, query_path=""):
    try:
        if action == "validate":
            json.loads(data)
            return {"success": True, "valid": True, "message": "有效的JSON"}
        if action == "format":
            obj = json.loads(data)
            return {"success": True, "formatted": json.dumps(obj, indent=2, ensure_ascii=False)}
        if action == "flatten":
            obj = json.loads(data)
            def _flatten(o, prefix=""):
                items = {}
                for k, v in o.items():
                    p = f"{prefix}.{k}" if prefix else k
                    if isinstance(v, dict):
                        items.update(_flatten(v, p))
                    else:
                        items[p] = v
                return items
            return {"success": True, "flattened": _flatten(obj)}
        if action == "query":
            obj = json.loads(data)
            parts = [p for p in query_path.replace("$.","").split(".") if p]
            result = obj
            for p in parts:
                if "[" in p:
                    name, idx = p.split("[")
                    idx = int(idx.strip("]"))
                    result = result.get(name, [])[idx]
                else:
                    result = result.get(p) if isinstance(result, dict) else result[int(p)]
            return {"success": True, "result": result}
        return {"success": False, "error": f"未知操作: {action}"}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON解析错误: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def main():
    while True:
        line = sys.stdin.readline()
        if not line: break
        line = line.strip()
        if not line: continue
        try:
            req = json.loads(line)
            resp = await handle_mcp(req)
            if resp:
                sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                sys.stdout.flush()
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.stderr.flush()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
