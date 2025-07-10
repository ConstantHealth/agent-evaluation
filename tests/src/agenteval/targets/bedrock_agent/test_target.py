import uuid

import pytest

from agenteval.targets.bedrock_agent import BedrockAgentTarget
from agenteval.utils import aws


@pytest.fixture
def bedrock_agent_fixture(mocker):
    mocker.patch.object(aws.boto3, "Session")

    fixture = BedrockAgentTarget(
        bedrock_agent_id="test-agent-id",
        bedrock_agent_alias_id="test-alias-id",
        aws_profile="test-profile",
        aws_region="us-west-2",
        bedrock_session_attributes={"first_name": "user_name"},
        bedrock_prompt_session_attributes={"timezone": "0"},
    )

    return fixture


class TestBedrockAgentTarget:
    def test_session_id(self, bedrock_agent_fixture):
        try:
            uuid.UUID(bedrock_agent_fixture._session_id)
            assert True
        except ValueError:
            assert False

    def test_invoke(self, mocker, bedrock_agent_fixture):
        mock_invoke_agent = mocker.patch.object(
            bedrock_agent_fixture.boto3_client, "invoke_agent"
        )

        mock_invoke_agent.return_value = {
            "completion": [
                {"chunk": {"bytes": b"test "}},
                {
                    "chunk": {
                        "bytes": b"completion",
                    },
                    "trace": {"trace": {"preProcessingTrace": None}},
                },
            ]
        }

        response = bedrock_agent_fixture.invoke("test prompt")

        assert response.response == "test completion"
        assert response.data == {
            "bedrock_agent_trace": [{"preProcessingTrace": None}],
            "bedrock_agent_citations": [],
            "bedrock_agent_return_control": None,
        }

    def test_invoke_with_return_control_event(self, mocker, bedrock_agent_fixture):
        mock_invoke_agent = mocker.patch.object(
            bedrock_agent_fixture.boto3_client, "invoke_agent"
        )

        mock_invoke_agent.return_value = {
            "completion": [
                {"chunk": {"bytes": b"Please provide "}},
                {
                    "chunk": {"bytes": b"your name"},
                    "returnControl": {
                        "invocationId": "test-invocation-id",
                        "invocationInputs": [
                            {
                                "apiInvocationInput": {
                                    "actionGroup": "test-action-group",
                                    "apiPath": "/test/path",
                                    "parameters": [
                                        {
                                            "name": "name",
                                            "type": "string",
                                            "value": "Please provide your name"
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                },
            ]
        }

        response = bedrock_agent_fixture.invoke("test prompt")

        assert response.response == "Please provide your name"
        assert response.data["bedrock_agent_return_control"] == {
            "invocationId": "test-invocation-id",
            "invocationInputs": [
                {
                    "apiInvocationInput": {
                        "actionGroup": "test-action-group",
                        "apiPath": "/test/path",
                        "parameters": [
                            {
                                "name": "name",
                                "type": "string",
                                "value": "Please provide your name"
                            }
                        ]
                    }
                }
            ]
        }

    def test_invoke_with_return_control_results(self, mocker, bedrock_agent_fixture):
        mock_invoke_agent = mocker.patch.object(
            bedrock_agent_fixture.boto3_client, "invoke_agent"
        )

        mock_invoke_agent.return_value = {
            "completion": [
                {"chunk": {"bytes": b"Thank you, "}},
                {"chunk": {"bytes": b"John!"}},
            ]
        }

        return_control_results = [
            {
                "invocationId": "test-invocation-id",
                "invocationInputs": [
                    {
                        "apiInvocationInput": {
                            "actionGroup": "test-action-group",
                            "apiPath": "/test/path",
                            "parameters": [
                                {
                                    "name": "name",
                                    "type": "string",
                                    "value": "Please provide your name"
                                }
                            ]
                        }
                    }
                ],
                "invocationResults": [
                    {
                        "apiResult": {
                            "actionGroupInvocationOutput": {
                                "json": {"name": "John"}
                            }
                        }
                    }
                ]
            }
        ]

        response = bedrock_agent_fixture.invoke("", return_control_results=return_control_results)

        # Verify that invoke_agent was called with returnControlInvocationResults
        mock_invoke_agent.assert_called_once()
        call_args = mock_invoke_agent.call_args[1]
        assert "returnControlInvocationResults" in call_args["sessionState"]
        assert call_args["sessionState"]["returnControlInvocationResults"] == return_control_results
        assert "inputText" not in call_args  # inputText should be omitted when returnControlInvocationResults is provided

        assert response.response == "Thank you, John!"

    def test_handle_return_control(self, mocker, bedrock_agent_fixture):
        mock_invoke_agent = mocker.patch.object(
            bedrock_agent_fixture.boto3_client, "invoke_agent"
        )

        mock_invoke_agent.return_value = {
            "completion": [
                {"chunk": {"bytes": b"Thank you, "}},
                {"chunk": {"bytes": b"John!"}},
            ]
        }

        return_control_data = {
            "invocationId": "test-invocation-id",
            "invocationInputs": [
                {
                    "apiInvocationInput": {
                        "actionGroup": "test-action-group",
                        "apiPath": "/test/path",
                        "parameters": [
                            {
                                "name": "name",
                                "type": "string",
                                "value": "Please provide your name"
                            }
                        ]
                    }
                }
            ]
        }

        user_inputs = [
            {
                "apiResult": {
                    "actionGroupInvocationOutput": {
                        "json": {"name": "John"}
                    }
                }
            }
        ]

        response = bedrock_agent_fixture.handle_return_control(return_control_data, user_inputs)

        # Verify that invoke_agent was called with the correct returnControlInvocationResults
        mock_invoke_agent.assert_called_once()
        call_args = mock_invoke_agent.call_args[1]
        assert "returnControlInvocationResults" in call_args["sessionState"]

        expected_results = [
            {
                "invocationId": "test-invocation-id",
                "invocationInputs": [return_control_data["invocationInputs"][0]],
                "invocationResults": [user_inputs[0]]
            }
        ]
        assert call_args["sessionState"]["returnControlInvocationResults"] == expected_results

        assert response.response == "Thank you, John!"
