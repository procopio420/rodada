"""Explicit protocol profiles; selection is not hardware certification."""

from dataclasses import dataclass

from .renderers import render_escpos, render_text


@dataclass(frozen=True)
class Profile:
    raw: bool
    encoding: str
    cut: bool = False
    minimum_agent: str = "0.3.0"


PROFILES = {
    "windows-driver-v1": Profile(False, "utf-8"),
    "escpos-ascii-v1": Profile(True, "ascii"),
    "escpos-pc860-v1": Profile(True, "cp860", minimum_agent="0.5.0"),
    "escpos-pc860-cut-v1": Profile(True, "cp860", cut=True, minimum_agent="0.5.0"),
}


def supports(version, profile_id):
    profile = PROFILES.get(profile_id)
    return profile is not None and version in ("0.3.0", "0.5.0") and (
        profile.minimum_agent == "0.3.0" or version == "0.5.0"
    )


def render_profile(profile_id, document, width_mm, reprint=False):
    profile = PROFILES[profile_id]
    if not profile.raw:
        return render_text(document, width_mm, reprint).encode("utf-8")
    if profile.encoding == "ascii":
        return render_escpos(document, width_mm, reprint, cut=False)
    # PC860 uses table 3 on this declared ESC/POS profile; verify on actual device.
    text = render_text(document, width_mm, reprint)
    text = text.replace("—", "-").replace("·", ".").replace("“", '"').replace("”", '"')
    return b"\x1b@\x1bt\x03" + text.encode("cp860", errors="replace") + b"\n\n\n" + (
        b"\x1dV\x00" if profile.cut else b""
    )
