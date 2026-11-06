"""Resolve only the two known CycloneDX schema references for offline Test-Json.

No validation constraints are removed. Emit an audit derivative, never replace
the source schema, SBOM, installed package or runtime configuration.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys


def bundle(root, spdx, jsf):
    result = copy.deepcopy(root)
    assert "AETHON_SPDX" not in result["definitions"] and "AETHON_JSF" not in result["definitions"]
    def visit(value, prefix=None):
        if isinstance(value, dict):
            value.pop("$id", None)
            if "$ref" in value:
                ref = value["$ref"]
                if ref.startswith("#") and prefix: value["$ref"] = prefix + ref[1:]
                elif ref.startswith("spdx"):
                    assert ref in {"spdx.schema.json", "spdx.SNAPSHOT.schema.json"}
                    value["$ref"] = "#/definitions/AETHON_SPDX"
                elif ref.startswith("jsf-"):
                    assert ref in {"jsf-0.82.schema.json#/definitions/signature", "jsf-0.82.SNAPSHOT.schema.json#/definitions/signature"}
                    value["$ref"] = "#/definitions/AETHON_JSF/definitions/signature"
                elif not ref.startswith("#"): raise ValueError("Unexpected external schema reference")
            for child in value.values(): visit(child, prefix)
        elif isinstance(value, list):
            for child in value: visit(child, prefix)
    visit(result)
    spdx, jsf = copy.deepcopy(spdx), copy.deepcopy(jsf)
    visit(spdx, "#/definitions/AETHON_SPDX")
    visit(jsf, "#/definitions/AETHON_JSF")
    result["definitions"]["AETHON_SPDX"] = spdx
    result["definitions"]["AETHON_JSF"] = jsf
    return result


if __name__ == "__main__":
    source, destination = map(Path, sys.argv[1:])
    names = ["bom-1.5.schema.json", "spdx.schema.json", "jsf-0.82.schema.json"]
    documents = [json.loads((source / n).read_text()) for n in names]
    with destination.open("x", encoding="utf8") as stream:
        json.dump(bundle(*documents), stream)
    print(json.dumps({"source_sha256": {n: hashlib.sha256((source / n).read_bytes()).hexdigest() for n in names},
                      "derived_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                      "scope": "Reference resolution only; normative constraints preserved"}))
