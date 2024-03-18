# content of conftest.py
import pytest

def pytest_addoption(parser):
    parser.addoption("--endpoint", action="store", help="grpc endpoint")
    parser.addoption("--device", action="store")
    parser.addoption("--tls-mutual", action="store_true")
    parser.addoption("--tls", action="store_true")
    parser.addoption("--ssl-name-server-override", action="store")

