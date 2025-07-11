# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
import uuid
from typing import Optional

from agenteval.targets import Boto3Target, TargetResponse

_SERVICE_NAME = "bedrock-agent-runtime"
logger = logging.getLogger(__name__)


class BedrockAgentTarget(Boto3Target):
    """A target encapsulating an Amazon Bedrock agent."""

    def __init__(
        self,
        bedrock_agent_id: str,
        bedrock_agent_alias_id: str,
        bedrock_session_attributes: Optional[dict] = {},
        bedrock_prompt_session_attributes: Optional[dict] = {},
        return_control_hook=None,
        **kwargs
    ):
        """Initialize the target.

        Args:
            bedrock_agent_id (str): The unique identifier of the Bedrock agent.
            bedrock_agent_alias_id (str): The alias of the Bedrock agent.
            bedrock_session_attributes Optional (dict): The dictionary of attributes that persist over a session between a user and agent
            bedrock_prompt_session_attributes Optional (dict): The dictionary of attributes that persist over a single turn (one InvokeAgent call)
            return_control_hook: Optional hook for return control
        """
        super().__init__(boto3_service_name=_SERVICE_NAME, **kwargs)
        self._bedrock_agent_id = bedrock_agent_id
        self._bedrock_agent_alias_id = bedrock_agent_alias_id
        self._session_state = {}
        if bedrock_session_attributes:
            self._session_state["sessionAttributes"] = bedrock_session_attributes
        if bedrock_prompt_session_attributes:
            self._session_state["promptSessionAttributes"] = (
                bedrock_prompt_session_attributes
            )
        self._session_id: str = str(uuid.uuid4())
        self._return_control_hook = return_control_hook
        self._trace_data = []
        self._citations = []

    def invoke(self, prompt: str) -> TargetResponse:
        response = self.boto3_client.invoke_agent(
            enableTrace=True,
            agentId=self._bedrock_agent_id,
            agentAliasId=self._bedrock_agent_alias_id,
            sessionId=self._session_id,
            inputText=prompt,
            sessionState=self._session_state,
        )

        try:
            return self.handle_response(response)
        except Exception as e:
            logger.error(f"Error handling Bedrock Agent response: {e}")
            raise e

    def handle_response(self, response: dict) -> TargetResponse:
        stream = response["completion"]
        completion = ""

        for event in stream:
            logger.debug(f"Event: {list(event.keys())}")

            if chunk := event.get("chunk"):
                completion += chunk["bytes"].decode()
                if chunk.get("citations"):
                    self._citations.append(chunk["citations"])

            elif trace := event.get("trace"):
                self._trace_data.append(trace["trace"])

            elif return_control := event.get("returnControl"):
                logger.debug(f"Return control event received: {return_control}")
                return self.handle_return_control(return_control)

        data = {
            "bedrock_agent_trace": self._trace_data,
        }
        if self._citations:
            data["bedrock_agent_citations"] = self._citations

        logger.debug(f"Invoke Agent Completed: {completion}")

        return TargetResponse(
            response=completion,
            data=data
        )

    def handle_return_control(self, return_control: dict) -> TargetResponse:
        if not self._return_control_hook:
            # No return control hook, continue normally
            logger.warning("Return control event received but no hook configured")
            return TargetResponse(
                response="",
                data={"return_control_handled": False}
            )

        invocation_id = return_control["invocationId"]
        invocation_inputs = return_control["invocationInputs"]
        logger.debug(f"Processing return control with {len(invocation_inputs)} invocation inputs")

        invocation_results = []
        for invocation_input in invocation_inputs:
            mock_response = self._return_control_hook.get_response_for_invocation(invocation_input)

            if mock_response is None:
                logger.warning(f"No mock response found for invocation: {invocation_input}")
                continue

            logger.debug(f"Found mock response for invocation: {invocation_input}")

            invocation_result = {}
            if invocation_input.get("apiInvocationInput"):
                input = invocation_input["apiInvocationInput"]
                invocation_result = {
                    "apiResult": {
                        "actionGroup": input["actionGroup"],
                        "apiPath": input["apiPath"],
                        "httpMethod": input["httpMethod"],
                        "responseBody": {
                            "text": {
                                "body": mock_response
                            }
                        }
                    }
                }
            elif invocation_input.get("functionInvocationInput"):
                input = invocation_input["functionInvocationInput"]
                invocation_result = {
                    "functionResult": {
                        "actionGroup": input["actionGroup"],
                        "function": input["function"],
                        "responseBody": {
                            "TEXT": {
                                "body": mock_response
                            }
                        }
                    }
                }
            invocation_results.append(invocation_result)

        if not invocation_results:
            logger.warning("No invocation results found for return control")
            return TargetResponse(
                response="",
                data={"return_control_handled": False}
            )

        response = self.boto3_client.invoke_agent(
            enableTrace=True,
            agentId=self._bedrock_agent_id,
            agentAliasId=self._bedrock_agent_alias_id,
            sessionId=self._session_id,
            sessionState={
                "invocationId": invocation_id,
                "returnControlInvocationResults": invocation_results
            }
        )

        return self.handle_response(response)
