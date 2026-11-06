"""Bounded PE/ELF header parsing only. No native loading or subprocess execution."""
import re
import struct


def unpack(data, fmt, offset):
    if offset < 0 or offset+struct.calcsize(fmt) > len(data): raise ValueError("Native header out of bounds")
    return struct.unpack_from(fmt, data, offset)


def cstring(data, offset, limit=512):
    if not 0 <= offset < len(data): raise ValueError("Native string offset out of bounds")
    end = data.find(b"\0", offset, min(len(data), offset+limit))
    if end < 0: raise ValueError("Unterminated native string")
    value = data[offset:end].decode("ascii", errors="replace")
    if any(ord(c) < 32 for c in value): raise ValueError("Native control string")
    return value


def pe_headers(data):
    if data[:2] != b"MZ": raise ValueError("Not PE")
    pe = unpack(data, "<I", 0x3c)[0]
    if data[pe:pe+4] != b"PE\0\0": raise ValueError("Invalid PE signature")
    machine, count = unpack(data, "<HH", pe+4)
    optional_size = unpack(data, "<H", pe+20)[0]
    optional = pe+24
    magic = unpack(data, "<H", optional)[0]
    if magic not in (0x20b, 0x10b) or not 0 < count <= 96: raise ValueError("Unsupported PE geometry")
    directories = optional+(112 if magic == 0x20b else 96)
    sections = []
    for n in range(count):
        offset = optional+optional_size+n*40
        raw_name, virtual_size, rva, size, pointer = unpack(data, "<8sIIII", offset)
        if pointer+size > len(data): raise ValueError("PE section outside file")
        sections.append({"name": raw_name.rstrip(b"\0").decode("ascii", errors="replace"), "rva": rva,
                         "virtual_size": virtual_size, "bytes": size, "offset": pointer})
    def rva_offset(rva):
        for section in sections:
            if section["rva"] <= rva < section["rva"]+section["bytes"]:
                return section["offset"]+rva-section["rva"]
        raise ValueError("Unmapped PE RVA")
    imports = []
    import_rva, import_size = unpack(data, "<II", directories+8)
    if import_rva:
        start = rva_offset(import_rva)
        for n in range(min(import_size//20+1, 256)):
            descriptor = unpack(data, "<IIIII", start+n*20)
            if not any(descriptor): break
            imports.append(cstring(data, rva_offset(descriptor[3])))
        else: raise ValueError("PE import limit/termination")
    delay_imports = []
    if optional_size >= (directories-optional)+14*8:
        delay_rva, delay_size = unpack(data, "<II", directories+13*8)
        if delay_rva:
            start = rva_offset(delay_rva)
            for n in range(min(delay_size//32+1, 256)):
                descriptor = unpack(data, "<IIIIIIII", start+n*32)
                if not any(descriptor): break
                if descriptor[0] & 1: delay_imports.append(cstring(data, rva_offset(descriptor[1])))
                else: delay_imports.append("UNSUPPORTED_VA_DELAY_IMPORT")
    return {"format": "PE", "machine_hex": hex(machine), "architecture": "x86_64" if machine == 0x8664 else "OTHER",
            "imports": sorted(set(imports)), "delay_imports": sorted(set(delay_imports)), "sections": sections,
            "scope": "STATIC_HEADERS_NOT_LOADER_RESOLUTION"}


def elf_headers(data):
    if data[:4] != b"\x7fELF" or data[4:6] != b"\x02\x01": raise ValueError("Only ELF64 little-endian supported")
    machine = unpack(data, "<H", 18)[0]
    table = unpack(data, "<Q", 40)[0]
    entry_size, count = unpack(data, "<HH", 58)
    if entry_size < 64 or not 0 < count <= 4096: raise ValueError("ELF section limit")
    sections = [unpack(data, "<IIQQQQIIQQ", table+n*entry_size) for n in range(count)]
    needed, soname, paths = [], [], []
    for section in sections:
        if section[1] != 6: continue  # SHT_DYNAMIC
        if section[6] >= len(sections): raise ValueError("ELF dynamic string link")
        strings = sections[section[6]]
        start, size = section[4:6]
        if size//16 > 65536 or start+size > len(data): raise ValueError("ELF dynamic limit")
        for n in range(size//16):
            tag, value = unpack(data, "<qQ", start+n*16)
            if tag == 0: break
            if tag in (1, 14, 15, 29):
                if value >= strings[5]: raise ValueError("ELF dynamic string bounds")
                result = cstring(data, strings[4]+value)
                (needed if tag == 1 else soname if tag == 14 else paths).append(result)
    return {"format": "ELF64", "machine": machine, "architecture": "x86_64" if machine == 62 else "OTHER",
            "needed": sorted(set(needed)), "soname": sorted(set(soname)), "rpath_runpath": sorted(set(paths)),
            "scope": "STATIC_DT_NEEDED_NOT_DYNAMIC_LOADING"}


def inspect_native(data):
    try:
        if data.startswith(b"MZ"): header = pe_headers(data)
        elif data.startswith(b"\x7fELF"): header = elf_headers(data)
        elif data.startswith(b"!<arch>\n"): header = {"format": "AR", "parse_status": "NOT_AUDITED"}
        else: header = {"format": "UNKNOWN", "parse_status": "NOT_AUDITED"}
    except (ValueError, struct.error) as exc:
        header = {"parse_status": "NOT_AUDITED", "error": str(exc)}
    literals = sorted(set(match.decode("ascii", errors="replace").strip() for match in re.findall(
        rb"(?:OpenSSL|LibreSSL|BoringSSL) [0-9][A-Za-z0-9 .+_-]{0,70}", data)))[:20]
    crates = sorted(set(m.decode("ascii") for m in re.findall(
        rb"(?:pyo3(?:-ffi|-build-config)?|openssl-sys|libffi(?:-sys)?)[-/ ][0-9]+\.[0-9]+(?:\.[0-9]+)?", data)))[:30]
    symbols = [name for name in ["ffi_call", "ffi_prep_cif", "libffi", "pyo3", "rustc", "OPENSSL_init_crypto", "OpenSSL_version"] if name.encode() in data]
    return {**header, "openssl_version_literals": literals, "crate_version_literals": crates,
            "reference_markers": symbols, "interpretation": "LITERALS_AND_HEADERS_ARE_EVIDENCE_NOT_COMPLETE_COMPONENT_OR_RUNTIME_PROOF"}
