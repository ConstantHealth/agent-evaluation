# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import uuid
from typing import Optional, List, Dict, Any

from agenteval.targets import Boto3Target, TargetResponse

_SERVICE_NAME = "bedrock-agent-runtime"


class BedrockAgentTarget(Boto3Target):
    """A target encapsulating an Amazon Bedrock agent."""

    def __init__(
        self,
        bedrock_agent_id: str,
        bedrock_agent_alias_id: str,
        bedrock_session_attributes: Optional[dict] = {},
        bedrock_prompt_session_attributes: Optional[dict] = {},
        **kwargs
    ):
        """Initialize the target.

        Args:
            bedrock_agent_id (str): The unique identifier of the Bedrock agent.
            bedrock_agent_alias_id (str): The alias of the Bedrock agent.
            bedrock_session_attributes Optional (dict): The dictionary of attributes that persist over a session between a user and agent
            bedrock_prompt_session_attributes Optional (dict): The dictionary of attributes that persist over a single turn (one InvokeAgent call)
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

    def invoke(self, prompt: str, return_control_results: Optional[List[Dict[str, Any]]] = None) -> TargetResponse:
        """Invoke the target with a prompt.

        Args:
            prompt (str): The prompt as a string.
            return_control_results (Optional[List[Dict[str, Any]]]): Results from previous returnControl events.
                If provided, this will be included in sessionState.returnControlInvocationResults and inputText will be ignored.

        Returns:
            TargetResponse
        """
        args = {
            "agentId": self._bedrock_agent_id,
            "agentAliasId": self._bedrock_agent_alias_id,
            "sessionId": self._session_id,
            "sessionState": self._session_state.copy(),
            "enableTrace": True,
        }

        # Handle returnControl results
        if return_control_results:
            args["sessionState"]["returnControlInvocationResults"] = return_control_results
            # When returnControlInvocationResults is provided, inputText is ignored
        else:
            args["inputText"] = prompt

        response = self.boto3_client.invoke_agent(**args)

        stream = response["completion"]
        completion = ""
        citations = []
        trace_data = []
        return_control_data = None

        for event in stream:
            chunk = event.get("chunk")
            event_trace = event.get("trace")
            return_control = event.get("returnControl")

            if chunk:
                completion += chunk.get("bytes").decode()
                if chunk.get("citations"):
                    citations.append(chunk.get("citations"))
            if event_trace:
                trace_data.append(event_trace.get("trace"))
            if return_control:
                return_control_data = return_control

        return TargetResponse(
            response=completion,
            data={
                "bedrock_agent_trace": trace_data,
                "bedrock_agent_citations": citations,
                "bedrock_agent_return_control": return_control_data,
            },
        )

    def handle_return_control(self, return_control_data: Dict[str, Any], user_inputs: List[Dict[str, Any]]) -> TargetResponse:
        """Handle a returnControl event by providing the required inputs.

        Args:
            return_control_data (Dict[str, Any]): The returnControl data from the previous response.
            user_inputs (List[Dict[str, Any]]): The user's responses to the returnControl prompts.
                Each input should match the structure expected by the invocationInputs.

        Returns:
            TargetResponse: The agent's response after processing the returnControl inputs.
        """
        # Create returnControlInvocationResults from the user inputs
        return_control_results = []

        for i, user_input in enumerate(user_inputs):
            if i < len(return_control_data.get("invocationInputs", [])):
                # Match user input with the expected invocation input
                expected_input = return_control_data["invocationInputs"][i]
                result = {
                    "invocationId": return_control_data.get("invocationId"),
                    "invocationInputs": [expected_input],  # Use the expected structure
                    "invocationResults": [user_input]  # Use the user's input
                }
                return_control_results.append(result)

        # Invoke the agent with the returnControl results
        return self.invoke("", return_control_results=return_control_results)
