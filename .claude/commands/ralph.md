---
description: Implementa un issue de GitHub end-to-end (modelos → schemas → repositorios → servicios → endpoints → migración → tests → handoff). Uso: /ralph <número_de_issue>
---

Ejecuta el script de automatización Ralph para implementar el issue #$ARGUMENTS end-to-end.

Corre el siguiente comando bash y sigue su ejecución:

```bash
bash ralph/once.sh $ARGUMENTS
```

Si el script falla porque falta `GITHUB_TOKEN`, pídele al usuario que lo exporte:
```
export GITHUB_TOKEN=<su_token>
```

Si el script falla porque falta `jq` o `curl`, instálalos o usa la alternativa con `gh`:
```bash
GITHUB_REPO="${GITHUB_REPO:-JohnEduar/reservas-ia}"
gh issue view $ARGUMENTS --repo "$GITHUB_REPO" --json title,body,labels,comments
```

Una vez tengas el contenido del issue, implementa end-to-end siguiendo el orden:
1. Lee todos los archivos relevantes antes de editar cualquiera.
2. **Models** — agrega modelos SQLAlchemy en `backend/app/models/` si se necesitan.
3. **Schemas** — agrega schemas Pydantic v2 con patrón Create/Update/Response.
4. **Repository** — agrega clase que extiende `BaseRepository`.
5. **Service** — agrega servicio con clases de excepciones tipadas. Sin try/except en servicios.
6. **Endpoints** — agrega router limpio. Sin try/except. Registra en `backend/app/api/v1/router.py`.
7. **Exception handler** — agrega nuevas excepciones a `_EXCEPTION_STATUS_MAP` en `backend/app/core/exception_handlers.py`.
8. **Migration** — crea migración Alembic con nombre descriptivo. Ajusta `down_revision` a la última migración existente.
9. **Tests** — agrega `backend/tests/test_<feature>.py`. Cubre: happy path, 401, 403, 404, 409, 422 según aplique.
10. **Handoff** — agrega entrada en `handoffs.md` describiendo lo construido.

No hagas commit. No inicies el servidor.
