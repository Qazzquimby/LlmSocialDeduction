from pydantic2ts import generate_typescript_defs

if __name__ == "__main__":
    generate_typescript_defs(
        "message_types.py",
        "../front/src/lib/types.ts",
    )
