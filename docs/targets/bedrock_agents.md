# Agents for Amazon Bedrock

Agents for Amazon Bedrock offers you the ability to build and configure autonomous agents in your application. For more information, visit the AWS documentation [here](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html).

## Prerequisites

The principal must have the following permissions:

- [InvokeAgent](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent-runtime_InvokeAgent.html)

## Configurations

```yaml title="agenteval.yml"
target:
  type: bedrock-agent
  bedrock_agent_id: my-agent-id
  bedrock_agent_alias_id: my-alias-id
  bedrock_session_attributes:
    first_name: user-name
  bedrock_prompt_session_attributes:
    timezone: user-timezone
```

`bedrock_agent_id` *(string)*

The unique identifier of the Bedrock agent.

---

`bedrock_agent_alias_id` *(string)*

The alias of the Bedrock agent.

---

`bedrock_session_attributes`  *(map; optional)*

The attributes that persist over a session between a user and agent, with the same sessionId belong to the same session, as long as the session time limit (the idleSessionTTLinSeconds) has not been surpassed. For example:

```yaml
bedrock_session_attributes:
  first_name: user-name
```

---

`bedrock_prompt_session_attributes`  *(map; optional)*

The attributes that persist over a single call of InvokeAgent. For example:

```yaml
bedrock_prompt_session_attributes:
    timezone: user-timezone
```

## ReturnControl Events

The BedrockAgentTarget supports handling returnControl events, which occur when an action group is configured to return control to the user for additional input. This is useful for testing agents that require multi-turn interactions with action groups.

### Detecting ReturnControl Events

When a returnControl event occurs, the response will include returnControl data in the `bedrock_agent_return_control` field:

```python
from agenteval.targets import BedrockAgentTarget

target = BedrockAgentTarget(
    bedrock_agent_id="my-agent-id",
    bedrock_agent_alias_id="my-alias-id"
)

response = target.invoke("Please book a flight")

# Check if returnControl event occurred
if response.data and response.data.get("bedrock_agent_return_control"):
    return_control_data = response.data["bedrock_agent_return_control"]
    print(f"ReturnControl detected: {return_control_data}")
```

### Handling ReturnControl Events

To handle a returnControl event, use the `handle_return_control` method:

```python
# Example returnControl data from response
return_control_data = {
    "invocationId": "invocation-123",
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
                    }
                ]
            }
        }
    ]
}

# Provide user inputs for the returnControl
user_inputs = [
    {
        "apiResult": {
            "actionGroupInvocationOutput": {
                "json": {"destination": "New York"}
            }
        }
    }
]

# Handle the returnControl
response = target.handle_return_control(return_control_data, user_inputs)
```

### Programmatic Usage

For programmatic testing scenarios, you can also pass returnControl results directly to the `invoke` method:

```python
return_control_results = [
    {
        "invocationId": "invocation-123",
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
                        }
                    ]
                }
            }
        ],
        "invocationResults": [
            {
                "apiResult": {
                    "actionGroupInvocationOutput": {
                        "json": {"destination": "New York"}
                    }
                }
            }
        ]
    }
]

# When returnControlInvocationResults is provided, inputText is ignored
response = target.invoke("", return_control_results=return_control_results)
```

### Testing Multi-turn Interactions

You can use returnControl events to test complex multi-turn interactions:

```python
# First turn - agent requests information
response1 = target.invoke("Book a flight to New York")
return_control_data = response1.data.get("bedrock_agent_return_control")

if return_control_data:
    # Second turn - provide required information
    user_inputs = [
        {
            "apiResult": {
                "actionGroupInvocationOutput": {
                    "json": {
                        "destination": "New York",
                        "date": "2024-01-15",
                        "passengers": 2
                    }
                }
            }
        }
    ]

    response2 = target.handle_return_control(return_control_data, user_inputs)
    print(f"Final response: {response2.response}")
```

## Using ReturnControl with YAML Configuration

ReturnControl events work seamlessly with YAML-based test configurations. The target automatically detects and exposes returnControl data, which can be handled through the standard evaluation process.

### Basic YAML Configuration with ReturnControl

```yaml title="agenteval.yml"
evaluator:
  model: claude-3
target:
  type: bedrock-agent
  bedrock_agent_id: BEDROCK_AGENT_ID
  bedrock_agent_alias_id: BEDROCK_AGENT_ALIAS_ID
  bedrock_session_attributes:
    user_id: "test-user-123"
    session_type: "evaluation"

tests:
  flight_booking_test:
    steps:
    - Ask the agent to book a flight to New York
    expected_results:
    - The agent either books the flight successfully OR requests additional information via returnControl
    max_turns: 3
    initial_prompt: "Please book a flight to New York for next week"
```

### Advanced YAML Configuration with Hooks

For complex returnControl scenarios, you can use hooks to programmatically handle the returnControl events:

```yaml title="agenteval.yml"
evaluator:
  model: claude-3
target:
  type: bedrock-agent
  bedrock_agent_id: BEDROCK_AGENT_ID
  bedrock_agent_alias_id: BEDROCK_AGENT_ALIAS_ID

tests:
  return_control_with_hook:
    steps:
    - Ask the agent to book a flight with specific requirements
    expected_results:
    - The agent successfully books the flight with all required parameters
    - The agent handles returnControl scenarios appropriately
    max_turns: 5  # Increased for multi-turn returnControl handling
    initial_prompt: "Book me a flight from Seattle to New York for March 15th, 2024"
    hook: samples.hooks.return_control_handler.ReturnControlHandler
```

### Hook Implementation for ReturnControl

Create a custom hook to handle returnControl events programmatically:

```python title="my_return_control_hook.py"
from typing import Dict, Any, Optional
from agenteval.hook import Hook
from agenteval.test import TestResult

class ReturnControlHandler(Hook):
    def on_conversation_turn(self, test_result: TestResult, turn_index: int,
                           user_message: str, agent_response: str,
                           response_data: Optional[Dict[str, Any]] = None) -> Optional[str]:

        # Check if this response contains returnControl data
        if response_data and response_data.get("bedrock_agent_return_control"):
            return_control_data = response_data["bedrock_agent_return_control"]

            # Handle the returnControl based on the action group
            return self._handle_return_control(return_control_data)

        return None

    def _handle_return_control(self, return_control_data: Dict[str, Any]) -> Optional[str]:
        # Provide appropriate responses based on the action group
        invocation_inputs = return_control_data.get("invocationInputs", [])

        for input_item in invocation_inputs:
            if "apiInvocationInput" in input_item:
                api_input = input_item["apiInvocationInput"]
                action_group = api_input.get("actionGroup", "")

                if "flight" in action_group.lower():
                    return "Flight details: Destination: New York, Date: 2024-03-15, Passengers: 1"
                elif "meeting" in action_group.lower():
                    return "Meeting details: Participants: team@company.com, Duration: 60 minutes"

        return None
```

### Best Practices for YAML-based ReturnControl Testing

1. **Increase max_turns**: Set `max_turns` to a higher value (3-6) to accommodate multi-turn returnControl flows.

2. **Use descriptive expected_results**: Write expected results that account for both successful completion and returnControl scenarios.

3. **Leverage hooks for complex scenarios**: Use custom hooks when you need programmatic control over returnControl responses.

4. **Test different action groups**: Create separate tests for different types of action groups to ensure comprehensive coverage.

5. **Monitor response data**: The returnControl data is automatically included in the response, allowing you to analyze the agent's behavior.

### Example Test Scenarios

```yaml title="comprehensive_return_control_tests.yml"
evaluator:
  model: claude-3
target:
  type: bedrock-agent
  bedrock_agent_id: BEDROCK_AGENT_ID
  bedrock_agent_alias_id: BEDROCK_AGENT_ALIAS_ID

tests:
  # Test 1: Simple returnControl detection
  flight_booking_request:
    steps:
    - Ask the agent to book a flight to New York
    expected_results:
    - The agent either books the flight successfully OR requests additional information via returnControl
    max_turns: 3
    initial_prompt: "Please book a flight to New York for next week"

  # Test 2: Agent should handle returnControl gracefully
  return_control_handling:
    steps:
    - Ask the agent to perform a task that requires action group parameters
    expected_results:
    - The agent responds appropriately when returnControl is needed
    - The agent provides clear information about what parameters are required
    max_turns: 2
    initial_prompt: "I need to schedule a meeting with the team"

  # Test 3: Complex multi-parameter request
  complex_parameter_request:
    steps:
    - Request the agent to create a comprehensive report with multiple parameters
    expected_results:
    - The agent identifies all required parameters
    - The agent structures the returnControl request clearly
    - The agent provides helpful guidance on what information is needed
    max_turns: 3
    initial_prompt: "Create a comprehensive quarterly sales report for Q1 2024"
    hook: samples.hooks.return_control_handler.ReturnControlHandler
```
