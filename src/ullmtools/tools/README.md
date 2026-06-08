# Tools Documentation

This document defines how tools should be created and documents the tools currently available in this project.

## 1. Goal

Provide a clear contract for tool calling:

- Runtime function behavior
- Tool schema contract
- Input and output format
- Limits and expected errors

## 2. Location

- Runtime: `src/assistant/tools/tools.py`
- Package init: `src/assistant/tools/__init__.py`

## 3. How To Create A New Tool

Follow this checklist.

1. Add one Python function in `tools.py`.
2. Add one schema constant in `tools.py` (OpenAI function calling format).
3. Keep the function name and schema `function.name` identical.
4. Keep parameters explicit (`type`, `properties`, `required`).
5. Return compact payloads (important for MicroPython memory limits).
6. Add docs for the new tool in section "Current Tools" below.
7. Register schema + execution route in the LLM/chat orchestration layer.

## 4. Template

```python
def my_tool(param1, param2=None):
    # Keep execution deterministic when possible.
    return {
        "ok": True,
        "value": "result"
    }


MY_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "my_tool",
        "description": "Short action-oriented description",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Required parameter"
                },
                "param2": {
                    "type": "string",
                    "description": "Optional parameter"
                }
            },
            "required": ["param1"]
        }
    }
}
```

## 5. Documentation Style For Each Tool

Use this structure for every tool:

1. Name
2. Purpose
3. Signature
4. Parameters
5. Return
6. Schema
7. Example input
8. Example output
9. Limitations

## 6. Current Tools

### Tool: get_temperature

Purpose:
Return a temperature sentence for a city.

Signature:

```python
def get_temperature(city):
    return "28 degrees Celsius in {}".format(city)
```

Parameters:

- `city` (string, required): City name.

Return:

- `string` with current fixed format:
    `28 degrees Celsius in <city>`

Schema:

```python
GET_TEMPERATURE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_temperature",
        "description": "Returns the current temperature for a city",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name"
                }
            },
            "required": ["city"]
        }
    }
}
```

Example tool call arguments:

```json
{
  "city": "Sao Paulo"
}
```

Expected output:

```text
28 degrees Celsius in Sao Paulo
```

Limitations:

- Mocked value (always `28`).
- No external weather API.
- No unit conversion.
- No validation for empty city.
