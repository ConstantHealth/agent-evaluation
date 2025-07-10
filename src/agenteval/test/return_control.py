# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Optional, Union
from pydantic import BaseModel, Field


class InvocationParameter(BaseModel):
    """A parameter for an API or function invocation."""

    name: str
    type: str
    value: Union[str, int, float, bool]


class ApiInvocationInput(BaseModel):
    """Expected API invocation input."""

    actionGroup: str
    apiPath: str
    httpMethod: str
    parameters: List[InvocationParameter] = Field(default_factory=list)


class FunctionInvocationInput(BaseModel):
    """Expected function invocation input."""

    actionGroup: str
    function: str
    parameters: List[InvocationParameter] = Field(default_factory=list)


class ExpectedInvocation(BaseModel):
    """Expected invocation configuration for return control."""

    apiInvocationInput: Optional[ApiInvocationInput] = None
    functionInvocationInput: Optional[FunctionInvocationInput] = None
    invocation_response_file: str


class TestStep(BaseModel):
    """A test step with optional return control configuration."""

    # do not collect as a pytest
    __test__ = False

    step: str
    expected_invocation: Optional[ExpectedInvocation] = None


class ReturnControlConfig(BaseModel):
    """Configuration for return control functionality."""

    enabled: bool = True
    response_files_dir: Optional[str] = None
