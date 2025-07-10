# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from typing import Dict, Any, Optional

from ..hook import Hook
from ..test import Test, TestResult
from ..trace import Trace
from ..utils.return_control import (
    load_response_file,
    match_invocation,
    match_trace_invocation
)
from ..test.return_control import ExpectedInvocation, TestStep

logger = logging.getLogger(__name__)


class ReturnControlHook(Hook):
    """A hook that implements return control functionality for agent testing."""

    def __init__(self, test: Test, base_dir: Optional[str] = None):
        """Initialize the return control hook.

        Args:
            test: The test case with return control configuration
            base_dir: Base directory for resolving response file paths
        """
        self.test = test
        self.base_dir = base_dir or os.getcwd()
        self.expected_invocations = []
        self.response_files = {}

        # Extract expected invocations from test steps
        for i, step in enumerate(test.steps):
            if isinstance(step, TestStep) and step.expected_invocation:
                self.expected_invocations.append({
                    'step_index': i,
                    'invocation': step.expected_invocation
                })

    def pre_evaluate(self, test: Test, trace: Trace) -> None:
        """Pre-evaluation setup for return control."""
        if not self.expected_invocations:
            return

        logger.info(f"Return control enabled for test '{test.name}' with {len(self.expected_invocations)} expected invocations")

        # Pre-load response files
        for expected in self.expected_invocations:
            invocation = expected['invocation']
            try:
                response_content = load_response_file(
                    invocation.invocation_response_file,
                    self.base_dir
                )
                self.response_files[invocation.invocation_response_file] = response_content
                logger.debug(f"Loaded response file: {invocation.invocation_response_file}")
            except Exception as e:
                logger.error(f"Failed to load response file {invocation.invocation_response_file}: {e}")
                raise

    def post_evaluate(self, test: Test, test_result: TestResult, trace: Trace) -> None:
        """Post-evaluation validation for return control."""
        if not self.expected_invocations:
            return

        trace_data = trace.steps
        return_control_invocations = []

        for step_data in trace_data:
            target_response_data = step_data.get('data')
            if not target_response_data:
                continue

            # Extract return control invocations from trace data
            for trace_event in target_response_data.get('bedrock_agent_trace', []):
                invocation_input = trace_event.get('orchestrationTrace', {}).get('invocationInput', {})
                if (invocation := invocation_input.get('actionGroupInvocationInput')) and invocation.get('executionType') == 'RETURN_CONTROL':
                    return_control_invocations.append(invocation)

        # Validate invocations
        validation_errors = []
        matched_invocations = set()

        for expected in self.expected_invocations:
            invocation = expected['invocation']
            step_index = expected['step_index']

            # Find matching actual invocation
            matched = False
            for actual_invocation in return_control_invocations:
                if match_trace_invocation(invocation, actual_invocation):
                    matched = True
                    matched_invocations.add(id(actual_invocation))
                    logger.debug(f"Matched expected invocation for step {step_index}")
                    break

            if not matched:
                validation_errors.append(
                    f"Step {step_index}: Expected invocation not found. "
                    f"Expected: {invocation.dict()}"
                )

        # Check for unexpected invocations
        unexpected_invocations = []
        for actual_invocation in return_control_invocations:
            if id(actual_invocation) not in matched_invocations:
                unexpected_invocations.append(actual_invocation)

        if unexpected_invocations:
            validation_errors.append(
                f"Found {len(unexpected_invocations)} unexpected invocations: {unexpected_invocations}"
            )

        # Update test result if validation failed
        if validation_errors:
            test_result.passed = False
            test_result.result = "RETURN_CONTROL_VALIDATION_FAILED"
            test_result.reasoning = "\n".join(validation_errors)
            logger.error(f"Return control validation failed for test '{test.name}': {validation_errors}")
        else:
            logger.info(f"Return control validation passed for test '{test.name}'")

    def get_response_for_invocation(self, invocation_data: Dict[str, Any]) -> Optional[Any]:
        """Get the response for a specific invocation.

        Args:
            invocation_data: The actual invocation data from the agent

        Returns:
            The response content if a match is found, None otherwise
        """

        for expected in self.expected_invocations:
            invocation = expected['invocation']
            if match_invocation(invocation, invocation_data):
                return self.response_files.get(invocation.invocation_response_file)

        return None
