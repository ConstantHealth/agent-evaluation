# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Optional, Union, List

from pydantic import BaseModel, computed_field, model_validator

from agenteval import defaults
from agenteval.test import Test
from agenteval.test.return_control import TestStep, ExpectedInvocation, ApiInvocationInput, FunctionInvocationInput, InvocationParameter


class TestSuite(BaseModel):
    """A collection of tests to be executed.

    Attributes:
        tests: A list of tests.
    """

    tests: list[Test]

    # do not collect as a pytest
    __test__ = False

    @model_validator(mode="after")
    def _check_test_names_unique(self) -> TestSuite:
        unique_names = len(set(test.name for test in self.tests))

        if unique_names != len(self.tests):
            raise ValueError("Test names must be unique")

        return self

    def __iter__(self):
        return iter(self.tests)

    @computed_field
    @property
    def num_tests(self) -> int:
        """Returns the number of tests in the test suite."""
        return len(self.tests)

    @classmethod
    def load(cls, config: dict[str, dict], filter: Optional[str]) -> TestSuite:
        """Loads a `TestSuite` from a list of test configurations and an optional filter.

        Args:
            config (dict[str, dict]): A dictionary of test configurations, where
                the keys are the test names and the values are the test cases as dictionaries.
            filter (Optional[str]): A filter string to apply when loading the tests.

        Returns:
            TestSuite: A `TestSuite` instance containing the loaded tests.
        """
        return cls(tests=TestSuite._load_tests(config, filter))

    @staticmethod
    def _load_tests(config: dict[str, dict], filter: Optional[str]) -> list[Test]:
        tests = []

        if filter:
            names = TestSuite._parse_filter(filter)
        else:
            names = config.keys()

        for name in names:
            test_config = config[name]
            steps = TestSuite._parse_steps(test_config["steps"])

            tests.append(
                Test(
                    name=name,
                    steps=steps,
                    expected_results=test_config["expected_results"],
                    initial_prompt=test_config.get("initial_prompt"),
                    max_turns=test_config.get("max_turns", defaults.MAX_TURNS),
                    hook=test_config.get("hook"),
                )
            )

        return tests

    @staticmethod
    def _parse_steps(steps_config: List[Union[str, dict]]) -> List[Union[str, TestStep]]:
        """Parse steps configuration into TestStep objects or strings."""
        parsed_steps = []

        for step_config in steps_config:
            if isinstance(step_config, str):
                # Simple string step
                parsed_steps.append(step_config)
            elif isinstance(step_config, dict):
                # Complex step with return control configuration
                step_text = step_config.get("step")
                if not step_text:
                    raise ValueError("Step configuration must contain 'step' field")

                expected_invocation = None
                if "expected_invocation" in step_config:
                    inv_config = step_config["expected_invocation"]

                    # Parse API invocation input
                    api_invocation = None
                    if "apiInvocationInput" in inv_config:
                        api_config = inv_config["apiInvocationInput"]
                        parameters = [
                            InvocationParameter(**param)
                            for param in api_config.get("parameters", [])
                        ]
                        api_invocation = ApiInvocationInput(
                            actionGroup=api_config["actionGroup"],
                            apiPath=api_config["apiPath"],
                            httpMethod=api_config["httpMethod"],
                            parameters=parameters
                        )

                    # Parse function invocation input
                    function_invocation = None
                    if "functionInvocationInput" in inv_config:
                        func_config = inv_config["functionInvocationInput"]
                        parameters = [
                            InvocationParameter(**param)
                            for param in func_config.get("parameters", [])
                        ]
                        function_invocation = FunctionInvocationInput(
                            actionGroup=func_config["actionGroup"],
                            function=func_config["function"],
                            parameters=parameters
                        )

                    expected_invocation = ExpectedInvocation(
                        apiInvocationInput=api_invocation,
                        functionInvocationInput=function_invocation,
                        invocation_response_file=inv_config["invocation_response_file"]
                    )

                test_step = TestStep(
                    step=step_text,
                    expected_invocation=expected_invocation
                )
                parsed_steps.append(test_step)
            else:
                raise ValueError(f"Invalid step configuration: {step_config}")

        return parsed_steps

    @staticmethod
    def _parse_filter(filter: str) -> list[str]:
        return [n.strip() for n in filter.split(",")]
