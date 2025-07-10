#!/usr/bin/env python3
"""
Example hook for handling returnControl events in YAML-based tests.

This hook demonstrates how to:
1. Detect returnControl events in agent responses
2. Provide appropriate responses for returnControl scenarios
3. Continue the conversation flow seamlessly
"""

from typing import Dict, Any, Optional
from agenteval.hook import Hook
from agenteval.test import TestResult


class ReturnControlHandler(Hook):
    """Hook to handle returnControl events in Bedrock agent tests."""

    def __init__(self, **kwargs):
        """Initialize the hook with configuration."""
        super().__init__(**kwargs)
        # Predefined responses for common returnControl scenarios
        self.default_responses = {
            "flight_booking": {
                "destination": "New York",
                "date": "2024-03-15",
                "passengers": 1,
                "class": "economy"
            },
            "meeting_scheduling": {
                "participants": ["team@company.com"],
                "duration": 60,
                "topic": "Project Review"
            },
            "report_generation": {
                "report_type": "quarterly",
                "period": "Q1 2024",
                "format": "PDF"
            }
        }

    def on_test_start(self, test_result: TestResult) -> None:
        """Called when a test starts."""
        print(f"Starting test: {test_result.test_name}")
        print("ReturnControl handler is active and ready to handle returnControl events")

    def on_conversation_turn(self, test_result: TestResult, turn_index: int,
                           user_message: str, agent_response: str,
                           response_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Called after each conversation turn.

        Args:
            test_result: The current test result
            turn_index: The index of the current turn (0-based)
            user_message: The user's message
            agent_response: The agent's response
            response_data: Additional response data (including returnControl info)

        Returns:
            Optional string message to send to the agent (for returnControl handling)
        """

        # Check if this response contains returnControl data
        if response_data and response_data.get("bedrock_agent_return_control"):
            return_control_data = response_data["bedrock_agent_return_control"]

            print(f"ReturnControl detected in turn {turn_index}")
            print(f"Invocation ID: {return_control_data.get('invocationId')}")

            # Handle the returnControl based on the action group
            return self._handle_return_control(return_control_data, test_result.test_name)

        return None

    def _handle_return_control(self, return_control_data: Dict[str, Any], test_name: str) -> Optional[str]:
        """
        Handle returnControl events by providing appropriate responses.

        Args:
            return_control_data: The returnControl data from the agent
            test_name: The name of the current test

        Returns:
            Optional string message to send to the agent
        """

        invocation_inputs = return_control_data.get("invocationInputs", [])

        for input_item in invocation_inputs:
            # Check for API invocation input
            if "apiInvocationInput" in input_item:
                api_input = input_item["apiInvocationInput"]
                action_group = api_input.get("actionGroup", "")
                api_path = api_input.get("apiPath", "")

                print(f"Action Group: {action_group}")
                print(f"API Path: {api_path}")

                # Provide appropriate response based on the action group
                if "flight" in action_group.lower() or "booking" in action_group.lower():
                    return self._format_flight_response(api_input)
                elif "meeting" in action_group.lower() or "schedule" in action_group.lower():
                    return self._format_meeting_response(api_input)
                elif "report" in action_group.lower():
                    return self._format_report_response(api_input)
                else:
                    # Generic response for unknown action groups
                    return self._format_generic_response(api_input)

        return None

    def _format_flight_response(self, api_input: Dict[str, Any]) -> str:
        """Format a response for flight booking returnControl."""
        parameters = api_input.get("parameters", [])
        response_parts = []

        for param in parameters:
            param_name = param.get("name", "")
            param_value = param.get("value", "")

            if "destination" in param_name.lower():
                response_parts.append(f"Destination: New York")
            elif "date" in param_name.lower():
                response_parts.append(f"Date: 2024-03-15")
            elif "passengers" in param_name.lower():
                response_parts.append(f"Passengers: 1")
            elif "class" in param_name.lower():
                response_parts.append(f"Class: economy")
            else:
                response_parts.append(f"{param_name}: {param_value}")

        return "Here are the flight details: " + ", ".join(response_parts)

    def _format_meeting_response(self, api_input: Dict[str, Any]) -> str:
        """Format a response for meeting scheduling returnControl."""
        return "Meeting details: Participants: team@company.com, Duration: 60 minutes, Topic: Project Review"

    def _format_report_response(self, api_input: Dict[str, Any]) -> str:
        """Format a response for report generation returnControl."""
        return "Report details: Type: quarterly, Period: Q1 2024, Format: PDF"

    def _format_generic_response(self, api_input: Dict[str, Any]) -> str:
        """Format a generic response for unknown action groups."""
        parameters = api_input.get("parameters", [])
        if parameters:
            param_names = [param.get("name", "unknown") for param in parameters]
            return f"Please provide the following information: {', '.join(param_names)}"
        return "I understand you need additional information. Please let me know what specific details you require."

    def on_test_end(self, test_result: TestResult) -> None:
        """Called when a test ends."""
        print(f"Test completed: {test_result.test_name}")
        if test_result.passed:
            print("✅ Test passed - returnControl handling was successful")
        else:
            print("❌ Test failed - check returnControl handling logic")
