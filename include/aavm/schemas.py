import os
import json

import aavm

_SCHEMAS_DIR = os.path.join(os.path.dirname(aavm.__file__), 'schemas')


def _get_schema(schema_fpath: str) -> dict:
    if not os.path.isfile(schema_fpath):
        raise FileNotFoundError(schema_fpath)
    with open(schema_fpath, 'r') as fin:
        return json.load(fin)


def get_machine_schema(schema: str) -> dict:
    schema_fpath = os.path.join(_SCHEMAS_DIR, "machine.json", f"{schema}.json")
    return _get_schema(schema_fpath)


def get_runtime_schema(schema: str) -> dict:
    schema_fpath = os.path.join(_SCHEMAS_DIR, "runtime.json", f"{schema}.json")
    return _get_schema(schema_fpath)


def get_index_schema(schema: str) -> dict:
    schema_fpath = os.path.join(_SCHEMAS_DIR, "index", f"{schema}.json")
    return _get_schema(schema_fpath)


__all__ = [
    "get_machine_schema",
    "get_runtime_schema",
    "get_index_schema"
]
