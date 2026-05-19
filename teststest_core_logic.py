from check_imports import run_import_check


def test_import_graph_connected():
    result = run_import_check()
    assert all(result.values())
