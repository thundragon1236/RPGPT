def test_import_app():
    try:
        from app import app
    except Exception as e:
        print("IMPORT ERROR:", e)
        assert False, f"Import failed: {e}"
