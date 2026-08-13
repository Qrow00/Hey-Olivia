"""Skills: the agent's executable capabilities. register_all() wires them up."""

from app.core.skill_registry import SkillRegistry


def register_all(reg: SkillRegistry) -> None:
    """Register every skill module into the registry."""
    from app.skills import (adb, browser, camera, code, docs, email, media,
                            scheduler, smart_home, system)

    for module in (system, smart_home, media, browser, email, docs, camera, adb,
                   code, scheduler):
        module.register(reg)
