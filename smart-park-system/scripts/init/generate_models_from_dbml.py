from pathlib import Path
from pydbml import PyDBML
import re

DBML_FILE = Path("docs/db/smart-park-db.md")
OUT_FILE = Path("backend/apps/core/models.py")

TYPE_MAP = {
    "bigint": "models.BigIntegerField",
    "bigserial": "models.BigAutoField",
    "serial": "models.AutoField",
    "uuid": "models.UUIDField",
    "varchar": "models.CharField",
    "text": "models.TextField",
    "boolean": "models.BooleanField",
    "bool": "models.BooleanField",
    "timestamptz": "models.DateTimeField",
    "timestamp": "models.DateTimeField",
    "int": "models.IntegerField",
    "integer": "models.IntegerField",
    "numeric": "models.DecimalField",
    "jsonb": "models.JSONField",
    "double": "models.FloatField",
    "inet": "models.GenericIPAddressField",
}


def snake_to_camel(s: str) -> str:
    parts = s.replace("-", "_").split("_")
    return "".join(p.capitalize() for p in parts if p)


def field_from_column(c):
    type_name, type_args = parse_dbml_type(c.type)
    base = TYPE_MAP.get(type_name, "models.TextField")
    args, kwargs = [], []

    # varchar/char length
    if ("char" in type_name) and type_args:
        kwargs.append(f"max_length={type_args[0]}")

    # numeric(p,s)
    if type_name == "numeric" and type_args:
        if len(type_args) == 2:
            kwargs.append(f"max_digits={type_args[0]}")
            kwargs.append(f"decimal_places={type_args[1]}")

    # nullability
    if getattr(c, "not_null", None) is False:
        kwargs += ["null=True", "blank=True"]

    # primary key
    if getattr(c, "pk", False):
        # Garante PK auto se for serial/bigserial; senão mantém base e só marca PK
        if "serial" in type_name:
            base = (
                "models.AutoField" if type_name == "serial" else "models.BigAutoField"
            )
        kwargs.append("primary_key=True")

    # defaults simples (ignora funções SQL cravadas no DB, que vem como `...`)
    default_val = getattr(c, "default", None)
    if isinstance(default_val, str) and not default_val.startswith("`"):
        kwargs.append(f"default='{default_val}'")
    elif isinstance(default_val, (int, float, bool)):
        kwargs.append(f"default={default_val}")

    return f"    {c.name} = {base}({', '.join(args + kwargs)})"


def build_fk_map(dbml):
    """
    fk_map[table_name][column_name] = referenced_table_name
    Compatível com pydbml 1.x (ou 0.4.x), usando Reference.col1/col2.
    Considera a direção do 'type': '<', '>', '-'
    """
    fk_map = {}

    # 1) A partir de refs globais
    for ref in getattr(dbml, "refs", []):
        cols_left = getattr(ref, "col1", []) or []
        cols_right = getattr(ref, "col2", []) or []
        for lcol, rcol in zip(cols_left, cols_right):
            if ref.type == "<":
                # table2.col2 -> table1.col1
                child_tbl, child_col = ref.table2.name, rcol.name
                parent_tbl = ref.table1.name
            elif ref.type == ">":
                # table1.col1 -> table2.col2
                child_tbl, child_col = ref.table1.name, lcol.name
                parent_tbl = ref.table2.name
            else:  # '-' (1-1). Por padrão, trate como table2 -> table1
                child_tbl, child_col = ref.table2.name, rcol.name
                parent_tbl = ref.table1.name

            fk_map.setdefault(child_tbl, {})[child_col] = parent_tbl

    # 2) (Opcional, reforço) Varre refs por tabela se necessário
    #    Útil se quiser garantir cobertura mesmo quando 'dbml.refs' estiver vazio
    for table in getattr(dbml, "tables", []):
        for tref in getattr(table, "refs", []):
            # TableReference: col (lista na tabela atual) -> ref_table/ref_col
            for col in getattr(tref, "col", []) or []:
                fk_map.setdefault(table.name, {})[col.name] = tref.ref_table.name

    return fk_map


def render_model(table, fk_map):
    class_name = snake_to_camel(table.name)
    lines = [f"class {class_name}(models.Model):"]

    table_fk_map = fk_map.get(table.name, {})

    for c in table.columns:
        ref_tbl = table_fk_map.get(c.name)
        if ref_tbl:
            to_model = snake_to_camel(ref_tbl)
            # on_delete: PROTECT por padrão (ajuste conforme regras de domínio)
            lines.append(
                f"    {c.name} = models.ForeignKey('{to_model}', on_delete=models.PROTECT, db_column='{c.name}')"
            )
        else:
            lines.append(field_from_column(c))

    lines.append("    class Meta:")
    lines.append(f"        db_table = '{table.name}'")
    lines.append("")
    return "\n".join(lines)


def parse_dbml_type(dbml_type):
    """
    Retorna (type_name: str, type_args: list).
    Aceita tanto objeto Type (c/ .name e .args) quanto string 'varchar(255)'.
    """
    # Caso seja o objeto Type do pydbml
    if hasattr(dbml_type, "name"):
        name = dbml_type.name.lower()
        args = list(getattr(dbml_type, "args", []) or [])
        return name, args

    # Caso seja string "numeric(10,2)", "varchar(80)", "double precision", etc.
    if isinstance(dbml_type, str):
        s = dbml_type.strip()
        m = re.match(r"([a-zA-Z ]+)\s*(?:\(([^)]+)\))?$", s)
        if m:
            name = m.group(1).strip().lower()
            raw_args = m.group(2)
            args = []
            if raw_args:
                for a in raw_args.split(","):
                    a = a.strip()
                    args.append(int(a) if a.isdigit() else a)
            return name, args
        return s.lower(), []

    # Fallback
    return "text", []


def main():
    dbml = PyDBML(DBML_FILE.read_text(encoding="utf-8"))
    fk_map = build_fk_map(dbml)
    out = ["from django.db import models", ""]
    for table in dbml.tables:
        out.append(render_model(table, fk_map))
    OUT_FILE.write_text("\n".join(out), encoding="utf-8")
    print(f"Generated: {OUT_FILE}")


if __name__ == "__main__":
    main()
