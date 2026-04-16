from pathlib import Path

base_path = Path("app")

for file in base_path.rglob("__init__.py"):
    try:
        content = file.read_text(errors="ignore")

        if not content.strip():
            print(f"Corrigindo vazio: {file}")
            file.write_text("# -*- coding: utf-8 -*-\n", encoding="utf-8")

    except Exception as e:
        print(f"Erro em {file}: {e}")