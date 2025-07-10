# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
import os
from typing import Any, Dict, Optional, Union
from pathlib import Path

from ..test.return_control import (
    ExpectedInvocation,
    ApiInvocationInput,
    FunctionInvocationInput,
)


def load_response_file(
    file_path: str, base_dir: Optional[str] = None
) -> Union[Dict[str, Any], str]:
    """
    Load a response file and return its contents.

    Args:
        file_path: Path to the response file
        base_dir: Base directory to resolve relative paths

    Returns:
        Raw content

    Raises:
        FileNotFoundError: If the response file doesn't exist
        ValueError: If the file format is not supported
    """
    if base_dir:
        full_path = os.path.join(base_dir, file_path)
    else:
        full_path = file_path

    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Response file not found: {full_path}")

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    return content


def _match_parameters(expected_params: Dict[str, Any], actual_params: list) -> bool:
    actual_param_dict = {p.get("name"): p.get("value") for p in actual_params}
    return actual_param_dict == expected_params


def match_api_invocation(expected: ApiInvocationInput, actual: Dict[str, Any]) -> bool:
    if (
        actual.get("actionGroup") != expected.actionGroup
        or actual.get("apiPath") != expected.apiPath
        or actual.get("httpMethod") != expected.httpMethod
    ):
        return False

    expected_params = {p.name: p.value for p in expected.parameters}
    return _match_parameters(expected_params, actual.get("parameters", []))


def match_function_invocation(
    expected: FunctionInvocationInput, actual: Dict[str, Any]
) -> bool:
    if (
        actual.get("actionGroup") != expected.actionGroup
        or actual.get("function") != expected.function
    ):
        return False

    expected_params = {p.name: p.value for p in expected.parameters}
    return _match_parameters(expected_params, actual.get("parameters", []))


def match_invocation(expected: ExpectedInvocation, actual: Dict[str, Any]) -> bool:
    if expected.apiInvocationInput:
        return match_api_invocation(
            expected.apiInvocationInput, actual["apiInvocationInput"]
        )
    elif expected.functionInvocationInput:
        return match_function_invocation(
            expected.functionInvocationInput, actual["functionInvocationInput"]
        )

    return False


def match_trace_invocation(expected: ExpectedInvocation, trace: Dict[str, Any]) -> bool:
    if expected.apiInvocationInput:
        actual_api_invocation = {
            "actionGroup": trace.get("actionGroupName"),
            "apiPath": trace.get("apiPath"),
            "httpMethod": trace.get("verb"),
            "parameters": trace.get("parameters", []),
        }
        return match_api_invocation(expected.apiInvocationInput, actual_api_invocation)
    elif expected.functionInvocationInput:
        actual_function_invocation = {
            "actionGroup": trace.get("actionGroupName"),
            "function": trace.get("function"),
            "parameters": trace.get("parameters", []),
        }
        return match_function_invocation(
            expected.functionInvocationInput, actual_function_invocation
        )

    return False
