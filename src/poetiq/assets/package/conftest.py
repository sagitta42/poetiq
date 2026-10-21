import json
from pathlib import Path
from pydantic import BaseModel
import pytest
import os

PATH_TO_ASSETS = Path(os.path.dirname(__file__))
PATH_TO_CONFIGS = PATH_TO_ASSETS / "configs"


class TestCase(BaseModel):
    answer: int
    message: str


def read_test_config(filename: str) -> TestCase:
    config_path = PATH_TO_CONFIGS / f"{filename}.json"
    with open(config_path) as f:
        dataset_info = TestCase(**json.load(f))
    return dataset_info


def get_test_case(filename) -> TestCase:
    test_case = read_test_config(filename)
    ret = [pytest.param(test_case, id=filename)]
    return ret


@pytest.fixture(params=get_test_case("test_case"))
def test_case_example(request) -> TestCase:
    return request.param
