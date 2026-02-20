import sys, traceback

def check(module_path, name):
    try:
        exec(f"import {module_path}")
        print(f"[OK] {name}")
        return True
    except Exception:
        print(f"[FAIL] {name}:")
        traceback.print_exc()
        print()
        return False

check("models.route", "models.route")
check("auth.authRoute", "auth.authRoute")
check("utils.route", "utils.route")
