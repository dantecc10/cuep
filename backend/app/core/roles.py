VALID_ROLES = {"admin", "coordinador", "subcoordinador", "tutor", "alumno"}

IMPORT_ROLES_BY_ACTOR = {
    "admin": {"admin", "coordinador", "tutor"},
    "coordinador": {"tutor"},
}


def allowed_import_roles(actor_role: str) -> set[str]:
    return IMPORT_ROLES_BY_ACTOR.get(actor_role, set())
