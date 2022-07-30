

def test_package_imports():
    try:
        from python_eyelink_parser.eyelinkparser import parse, defaulttraceprocessor
    except:
        assert False
