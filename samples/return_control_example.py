#!/usr/bin/env python3
"""
Example script demonstrating returnControl event handling with Bedrock agents.

This example shows how to:
1. Detect returnControl events in agent responses
2. Handle returnControl events by providing required inputs
3. Test multi-turn interactions with action groups
"""

import os
from agenteval.targets import BedrockAgentTarget


def main():
    """Demonstrate returnControl event handling."""

    # Initialize the Bedrock agent target
    # Replace with your actual agent ID and alias ID
    target = BedrockAgentTarget(
        bedrock_agent_id=os.getenv("BEDROCK_AGENT_ID", "your-agent-id"),
        bedrock_agent_alias_id=os.getenv("BEDROCK_AGENT_ALIAS_ID", "your-alias-id"),
        aws_region=os.getenv("AWS_REGION", "us-east-1")
    )

    print("=== Bedrock Agent ReturnControl Example ===\n")

    # Example 1: Basic invocation that might trigger returnControl
    print("1. Initial agent invocation...")
    response = target.invoke("Please book a flight to New York")

    print(f"Agent response: {response.response}")

    # Check for returnControl event
    if response.data and response.data.get("bedrock_agent_return_control"):
        return_control_data = response.data["bedrock_agent_return_control"]
        print(f"\nReturnControl detected!")
        print(f"Invocation ID: {return_control_data.get('invocationId')}")
        print(f"Number of required inputs: {len(return_control_data.get('invocationInputs', []))}")

        # Example 2: Handle the returnControl event
        print("\n2. Handling returnControl event...")

        # Simulate user providing the required information
        user_inputs = [
            {
                "apiResult": {
                    "actionGroupInvocationOutput": {
                        "json": {
                            "destination": "New York",
                            "date": "2024-01-15",
                            "passengers": 2,
                            "class": "economy"
                        }
                    }
                }
            }
        ]

        # Handle the returnControl
        final_response = target.handle_return_control(return_control_data, user_inputs)
        print(f"Final agent response: {final_response.response}")

    else:
        print("\nNo returnControl event detected in this response.")

    # Example 3: Direct returnControl results usage
    print("\n3. Using returnControl results directly...")

    return_control_results = [
        {
            "invocationId": "example-invocation-123",
            "invocationInputs": [
                {
                    "apiInvocationInput": {
                        "actionGroup": "flight-booking",
                        "apiPath": "/book-flight",
                        "parameters": [
                            {
                                "name": "destination",
                                "type": "string",
                                "value": "Please provide destination"
                            },
                            {
                                "name": "date",
                                "type": "string",
                                "value": "Please provide travel date"
                            }
                        ]
                    }
                }
            ],
            "invocationResults": [
                {
                    "apiResult": {
                        "actionGroupInvocationOutput": {
                            "json": {
                                "destination": "Los Angeles",
                                "date": "2024-02-01"
                            }
                        }
                    }
                }
            ]
        }
    ]

    # When returnControlInvocationResults is provided, inputText is ignored
    direct_response = target.invoke("", return_control_results=return_control_results)
    print(f"Direct returnControl response: {direct_response.response}")

    print("\n=== Example completed ===")


if __name__ == "__main__":
    main()
