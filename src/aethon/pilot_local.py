"""Local-only adapter for frozen generation/precision contracts."""
import os
from pathlib import Path

from aethon.generation import ExplicitCausalLMDriver
from aethon.pilot_collector import ContractError
from aethon.pilot_governance import digest
from aethon.prospective import fingerprint


def verify_assets(snapshot, target):
    root = Path(snapshot)
    if not root.is_absolute() or root.is_symlink() or root.name != target["model_revision"] or root.parent.name != "snapshots":
        raise ContractError("exact_local_snapshot_required")
    root = root.resolve(strict=True)
    actual = {}
    for name, expected in target["assets"].items():
        # HF snapshot files may be reviewed cache symlinks; hash their actual payload.
        path = root/name
        import hashlib
        hasher = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024*1024), b""): hasher.update(chunk)
        value = {"sha256": hasher.hexdigest(), "bytes": path.stat().st_size}
        if value != expected: raise ContractError("model_asset_drift")
        actual[name] = value
    return {"status": "PASS", "asset_set_sha256": fingerprint(actual)}


class LocalGenerationAdapter:
    def __init__(self, snapshot, target, config):
        verify_assets(snapshot, target)
        os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1")
        self.driver = ExplicitCausalLMDriver(str(snapshot), device="cpu", precision="float32", revision=config["revision"])
        self.torch = self.driver.torch
        self.torch.set_num_threads(4)
        if self.torch.get_num_interop_threads() != 1: self.torch.set_num_interop_threads(1)
        self.config = config
        self.tokenizer = self.driver.tokenizer
        if digest((self.tokenizer.chat_template or "").encode()) != config["template_sha256"]:
            raise ContractError("chat_template_drift")
        if self.driver.revision != config["revision"] or config["tokenizer_revision"] != Path(snapshot).name:
            raise ContractError("snapshot_revision_drift")
        if fingerprint(self.driver.model.generation_config.to_dict()) != config["effective_model_generation_config_sha256"]:
            raise ContractError("effective_model_configuration_drift")

    def prepare(self, messages, config):
        if config != self.config: raise ContractError("adapter_configuration_drift")
        if digest((self.tokenizer.chat_template or "").encode()) != config["template_sha256"]:
            raise ContractError("chat_template_drift")
        if fingerprint(self.driver.model.generation_config.to_dict()) != config["effective_model_generation_config_sha256"]:
            raise ContractError("effective_generation_config_drift")
        rendered = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        ids = self.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_dict=False)
        if self.tokenizer(rendered, add_special_tokens=False)["input_ids"] != ids:
            raise ContractError("tokenizer_chat_boundary_mismatch")
        return {"rendered_prompt": rendered, "input_ids": ids}

    def decode(self, ids, **kwargs): return self.tokenizer.decode(ids, **kwargs)

    def generate(self, request, config):
        self.torch.manual_seed(config["generation"]["seed"])
        result = self.driver.generate_result(request["prompt"], max_tokens=config["generation"]["max_new_tokens"],
                                             temperature=config["generation"]["temperature"], messages=request["messages"])
        # Tokenizer provenance is established by the verified snapshot-file set.
        metadata = {**result.metadata, "tokenizer_revision": config["tokenizer_revision"],
                    "tokenizer_provenance": "verified_snapshot_file_hashes"}
        from dataclasses import replace
        return replace(result, metadata=metadata)
