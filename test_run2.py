import subprocess, textwrap, sys, os

def run(inp: str) -> str:
    p = subprocess.run(
        [sys.executable, "run2.py"],
        input=inp.encode(),
        stdout=subprocess.PIPE,
        check=True,
    )
    return p.stdout.decode().strip()

def test_example1():
    inp = textwrap.dedent("""\
        a-b
        a-c
        b-D
        c-D
    """)
    assert run(inp).replace("\r\n", "\n") == "D-b\nD-c"

def test_example2():
    inp = textwrap.dedent("""\
        a-b
        b-c
        c-d
        b-A
        c-B
        d-C
    """)
    assert run(inp).replace("\r\n", "\n") == "A-b\nB-c\nC-d"

def test_example3():
    inp = textwrap.dedent("""\
        a-b
        b-c
        c-d
        c-e
        A-d
        A-e
        c-f
        c-g
        f-B
        g-B
    """)
    assert run(inp).replace("\r\n", "\n") == "A-d\nA-e\nB-f\nB-g"

def test_example4():
    inp = textwrap.dedent("""\
        a-B
    """)
    assert run(inp) == "B-a"

def test_example5():
    inp = textwrap.dedent("""\
        a-b
        b-C
        b-D
    """)
    assert run(inp).replace("\r\n", "\n") == "C-b\nD-b"
