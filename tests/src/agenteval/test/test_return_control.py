# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest
from agenteval.test import TestSuite
from agenteval.test.return_control import TestStep, ExpectedInvocation, ApiInvocationInput, FunctionInvocationInput, InvocationParameter


class TestReturnControl:
    """Test return control functionality."""

    def test_parse_simple_steps(self):
        """Test parsing simple string steps."""
        config = {
            "test1": {
                "steps": ["Step 1", "Step 2"],
                "expected_results": ["Result 1", "Result 2"],
                "max_turns": 5
            }
        }

        test_suite = TestSuite.load(config, None)
        assert len(test_suite.tests) == 1
        assert len(test_suite.tests[0].steps) == 2
        assert test_suite.tests[0].steps[0] == "Step 1"
        assert test_suite.tests[0].steps[1] == "Step 2"

    def test_parse_complex_steps_with_api_invocation(self):
        """Test parsing steps with API invocation configuration."""
        config = {
            "test1": {
                "steps": [
                    {
                        "step": "Ask agent what the weather is in Seattle?",
                        "expected_invocation": {
                            "apiInvocationInput": {
                                "actionGroup": "WeatherAPIs",
                                "apiPath": "/get-weather",
                                "httpMethod": "GET",
                                "parameters": [
                                    {
                                        "name": "location",
                                        "type": "string",
                                        "value": "Ottawa"
                                    },
                                    {
                                        "name": "date",
                                        "type": "string",
                                        "value": "2024-09-15"
                                    }
                                ]
                            },
                            "invocation_response_file": "samples/return_control/responses/weather_ottawa.json"
                        }
                    }
                ],
                "expected_results": ["The agent provides weather information for Ottawa"],
                "max_turns": 5
            }
        }

        test_suite = TestSuite.load(config, None)
        assert len(test_suite.tests) == 1
        assert len(test_suite.tests[0].steps) == 1

        step = test_suite.tests[0].steps[0]
        assert isinstance(step, TestStep)
        assert step.step == "Ask agent what the weather is in Seattle?"

        expected_invocation = step.expected_invocation
        assert expected_invocation is not None
        assert expected_invocation.apiInvocationInput is not None
        assert expected_invocation.functionInvocationInput is None
        assert expected_invocation.invocation_response_file == "samples/return_control/responses/weather_ottawa.json"

        api_invocation = expected_invocation.apiInvocationInput
        assert api_invocation.actionGroup == "WeatherAPIs"
        assert api_invocation.apiPath == "/get-weather"
        assert api_invocation.httpMethod == "GET"
        assert len(api_invocation.parameters) == 2
        assert api_invocation.parameters[0].name == "location"
        assert api_invocation.parameters[0].value == "Ottawa"
        assert api_invocation.parameters[1].name == "date"
        assert api_invocation.parameters[1].value == "2024-09-15"

    def test_parse_complex_steps_with_function_invocation(self):
        """Test parsing steps with function invocation configuration."""
        config = {
            "test1": {
                "steps": [
                    {
                        "step": "Now ask about the weather in Toronto",
                        "expected_invocation": {
                            "functionInvocationInput": {
                                "actionGroup": "WeatherAPIs",
                                "function": "get_weather",
                                "parameters": [
                                    {
                                        "name": "city",
                                        "type": "string",
                                        "value": "Toronto"
                                    },
                                    {
                                        "name": "country",
                                        "type": "string",
                                        "value": "CA"
                                    }
                                ]
                            },
                            "invocation_response_file": "samples/return_control/responses/weather_toronto.json"
                        }
                    }
                ],
                "expected_results": ["The agent provides weather information for Toronto"],
                "max_turns": 5
            }
        }

        test_suite = TestSuite.load(config, None)
        assert len(test_suite.tests) == 1
        assert len(test_suite.tests[0].steps) == 1

        step = test_suite.tests[0].steps[0]
        assert isinstance(step, TestStep)
        assert step.step == "Now ask about the weather in Toronto"

        expected_invocation = step.expected_invocation
        assert expected_invocation is not None
        assert expected_invocation.apiInvocationInput is None
        assert expected_invocation.functionInvocationInput is not None
        assert expected_invocation.invocation_response_file == "samples/return_control/responses/weather_toronto.json"

        function_invocation = expected_invocation.functionInvocationInput
        assert function_invocation.actionGroup == "WeatherAPIs"
        assert function_invocation.function == "get_weather"
        assert len(function_invocation.parameters) == 2
        assert function_invocation.parameters[0].name == "city"
        assert function_invocation.parameters[0].value == "Toronto"
        assert function_invocation.parameters[1].name == "country"
        assert function_invocation.parameters[1].value == "CA"

    def test_mixed_steps(self):
        """Test parsing a mix of simple and complex steps."""
        config = {
            "test1": {
                "steps": [
                    "Simple step 1",
                    {
                        "step": "Complex step with invocation",
                        "expected_invocation": {
                            "apiInvocationInput": {
                                "actionGroup": "TestAPI",
                                "apiPath": "/test",
                                "httpMethod": "GET",
                                "parameters": []
                            },
                            "invocation_response_file": "test_response.json"
                        }
                    },
                    "Simple step 2"
                ],
                "expected_results": ["Result 1", "Result 2"],
                "max_turns": 5
            }
        }

        test_suite = TestSuite.load(config, None)
        assert len(test_suite.tests) == 1
        assert len(test_suite.tests[0].steps) == 3

        # First step should be a string
        assert test_suite.tests[0].steps[0] == "Simple step 1"

        # Second step should be a TestStep
        assert isinstance(test_suite.tests[0].steps[1], TestStep)
        assert test_suite.tests[0].steps[1].step == "Complex step with invocation"

        # Third step should be a string
        assert test_suite.tests[0].steps[2] == "Simple step 2"

    def test_invalid_step_configuration(self):
        """Test that invalid step configuration raises an error."""
        config = {
            "test1": {
                "steps": [
                    {
                        "invalid_field": "This should fail"
                    }
                ],
                "expected_results": ["Result 1"],
                "max_turns": 5
            }
        }

        with pytest.raises(ValueError, match="Step configuration must contain 'step' field"):
            TestSuite.load(config, None)
