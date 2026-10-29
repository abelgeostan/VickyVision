import pytest
from app.tools.registry import get_tool_registry
from app.execution.local import LocalExecutionProvider
from app.execution.factory import get_execution_provider


def test_tool_registry_contains_required_tools():
    registry = get_tool_registry()
    tools = registry.list_tools()

    expected_tools = [
        "server.execute_command",
        "server.get_system_info",
        "server.get_resources",
        "server.list_processes",
        "server.read_file",
        "server.write_file",
        "server.edit_file",
        "server.search_files",
        "docker.list_containers",
        "docker.container_status",
        "docker.logs",
        "docker.start",
        "docker.stop",
        "docker.restart",
        "docker.build",
        "docker.compose",
        "docker.inspect",
        "git.status",
        "git.log",
        "git.diff",
        "git.branch",
        "git.pull",
        "git.checkout",
        "service.status",
        "service.start",
        "service.stop",
        "service.restart",
        "service.logs",
        "network.status",
        "network.connections",
        "filesystem.disk_usage",
    ]

    for expected in expected_tools:
        assert expected in tools, f"Missing required tool: {expected}"


def test_tool_parameter_validation():
    registry = get_tool_registry()
    provider = LocalExecutionProvider()

    # Missing required 'command' in execute_command
    res = registry.execute("server.execute_command", {}, provider)
    assert res.success is False
    assert "missing required argument" in res.error.lower() or "missing required parameter" in res.error.lower()

    # Missing required 'path' in read_file
    res2 = registry.execute("server.read_file", {}, provider)
    assert res2.success is False

    # Non-existent tool
    res3 = registry.execute("non_existent.tool", {}, provider)
    assert res3.success is False
    assert "not found" in res3.error.lower()


def test_server_file_operations_live():
    """Tests file write, read, targeted edit, and delete on the server."""
    registry = get_tool_registry()
    provider = get_execution_provider()

    test_path = "/tmp/vicky_techy_test.txt"

    # 1. Write file
    w_res = registry.execute(
        "server.write_file",
        {"path": test_path, "content": "line1: apple\nline2: banana\nline3: cherry\n"},
        provider,
    )
    assert w_res.success is True

    # 2. Read file
    r_res = registry.execute("server.read_file", {"path": test_path}, provider)
    assert r_res.success is True
    assert "banana" in r_res.raw_output

    # 3. Targeted Edit file
    e_res = registry.execute(
        "server.edit_file",
        {"path": test_path, "target": "banana", "replacement": "orange"},
        provider,
    )
    assert e_res.success is True

    # Verify edit
    r_res2 = registry.execute("server.read_file", {"path": test_path}, provider)
    assert "orange" in r_res2.raw_output
    assert "banana" not in r_res2.raw_output
    assert "apple" in r_res2.raw_output
    assert "cherry" in r_res2.raw_output

    # 4. Cleanup
    registry.execute("server.execute_command", {"command": f"rm -f {test_path}"}, provider)
