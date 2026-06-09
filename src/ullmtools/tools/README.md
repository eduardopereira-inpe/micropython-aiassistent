# Tools Documentation

This document defines how tools should be created and documents the tools currently available in this project.

## 1. Goal

Provide a clear contract for tool calling:

- Runtime function behavior
- Tool schema contract
- Input and output format
- Limits and expected errors

## 2. Location

- Runtime: `src/ullmtools/tools/*_tool.py`
- Package init: `src/ullmtools/tools/__init__.py`

## 3. How To Create A New Tool

Follow this checklist.

1. Create one file per tool, for example `my_tool.py`.
2. Implement one callable class that inherits from `CallableTool`.
3. Keep `NAME` and `_SCHEMA["function"]["name"]` identical.
4. Define `_SCHEMA` in the same class module (OpenAI function-calling format).
5. Keep parameters explicit (`type`, `properties`, `required`).
6. Return compact payloads (important for MicroPython memory limits).
7. Export the class in `src/ullmtools/tools/__init__.py`.
8. Register the tool instance with `llm.register_tool(tool=my_tool_instance)`.

## 4. Template

```python
from .base_tool import CallableTool


class MyTool(CallableTool):

    NAME = "my_tool"

    _SCHEMA = {
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
                "required": ["param1"],
                "additionalProperties": False
            }
        }
    }

    def __call__(self, param1, param2=None):
        return {
            "ok": True,
            "value": "result"
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
