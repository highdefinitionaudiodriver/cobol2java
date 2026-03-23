"""Shared fixtures for COBOL2Java tests."""
import os
import sys
import shutil
import tempfile
import pytest

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.cobol_parser import CobolParser
from src.oop_transformer import OopTransformer, TransformOptions
from src.java_generator import JavaCodeGenerator


SAMPLES_DIR = os.path.join(PROJECT_ROOT, "samples")


@pytest.fixture
def parser():
    return CobolParser(encoding="utf-8")


@pytest.fixture
def default_options():
    return TransformOptions(
        package_name="com.test",
        generate_getters_setters=True,
        use_big_decimal=True,
        generate_javadoc=True,
        extract_data_classes=True,
        extract_enums=True,
        extract_file_handlers=True,
        group_related_paragraphs=True,
    )


@pytest.fixture
def transformer(default_options):
    return OopTransformer(default_options)


@pytest.fixture
def generator(default_options):
    return JavaCodeGenerator(default_options)


@pytest.fixture
def output_dir():
    d = os.path.join(tempfile.gettempdir(), "cobol2java_pytest_output")
    if os.path.exists(d):
        shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d, exist_ok=True)
    yield d
    shutil.rmtree(d, ignore_errors=True)


def sample_path(filename):
    return os.path.join(SAMPLES_DIR, filename)
