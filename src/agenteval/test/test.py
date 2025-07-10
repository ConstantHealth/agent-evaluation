# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import Optional, Union, List

from pydantic import BaseModel, Field

from .return_control import TestStep, ReturnControlConfig


class Test(BaseModel, validate_assignment=True):
    """A test case.

    Attributes:
        name: Name of the test.
        steps: List of step to perform for the test. Can be strings or TestStep objects.
        expected_results: List of expected results for the test.
        initial_prompt: The initial prompt.
        max_turns: Maximum number of turns allowed for the test.
        hook: The module path to an evaluation hook.
        return_control: Configuration for return control functionality.
    """

    # do not collect as a pytest
    __test__ = False

    name: str
    steps: List[Union[str, TestStep]]
    expected_results: list[str]
    initial_prompt: Optional[str] = None
    max_turns: int
    hook: Optional[str] = None
    return_control: Optional[ReturnControlConfig] = None

    def get_step_text(self, step_index: int) -> str:
        """Get the step text, handling both string and TestStep formats."""
        step = self.steps[step_index]
        if isinstance(step, str):
            return step
        return step.step

    def get_expected_invocation(self, step_index: int):
        """Get the expected invocation for a step, if any."""
        step = self.steps[step_index]
        if isinstance(step, TestStep):
            return step.expected_invocation
        return None
