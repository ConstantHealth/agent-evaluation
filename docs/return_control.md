# Return Control

Return Control is a feature that allows you to define expected API or function invocations for your agent and provide mock responses for those invocations. This is particularly useful for testing agents that make external API calls or function invocations, as it allows you to control the responses without actually calling the external services.

## Overview

When return control is enabled, the framework will:

1. **Intercept invocations**: Monitor the agent's API and function invocations during testing
2. **Match expected invocations**: Compare actual invocations against your expected configurations
3. **Return mock responses**: Provide predefined responses from files instead of calling real services
4. **Validate behavior**: Ensure that the agent makes the expected invocations and fails the test if unexpected invocations occur

## Configuration

Return control is automatically enabled when you define `expected_invocation` in your test steps. You can configure it in your `agenteval.yml` file:

```yaml
evaluator:
  model: claude-3
target:
  type: bedrock-agent
  bedrock_agent_id: my-agent-id
  bedrock_agent_alias_id: my-alias-id
tests:
  weather_agent:
    max_turns: 5
    steps:
      - step: "Ask agent what the weather is in Seattle?"
        expected_invocation:
          apiInvocationInput:
            actionGroup: "WeatherAPIs"
            apiPath: "/get-weather"
            httpMethod: "GET"
            parameters:
              - name: "location"
                type: "string"
                value: "Ottawa"
              - name: "date"
                type: "string"
                value: "2024-09-15"
          invocation_response_file: "samples/return_control/responses/weather_ottawa.json"

      - step: "Now ask about the weather in Toronto"
        expected_invocation:
          functionInvocationInput:
            actionGroup: "WeatherAPIs"
            function: "get_weather"
            parameters:
              - name: "city"
                type: "string"
                value: "Toronto"
              - name: "country"
                type: "string"
                value: "CA"
          invocation_response_file: "samples/return_control/responses/weather_toronto.json"

    expected_results:
      - "The agent provides weather information for Ottawa"
      - "The agent provides weather information for Toronto"
```

## Step Configuration

Each step can be configured in two ways:

### Simple Steps (Backward Compatible)

```yaml
steps:
  - "Ask the agent a simple question"
  - "Follow up with another question"
```

### Complex Steps with Return Control

```yaml
steps:
  - step: "Ask the agent to get weather information"
    expected_invocation:
      # API invocation configuration
      apiInvocationInput:
        actionGroup: "WeatherAPIs"
        apiPath: "/get-weather"
        httpMethod: "GET"
        parameters:
          - name: "location"
            type: "string"
            value: "Seattle"
      # Function invocation configuration
      functionInvocationInput:
        actionGroup: "WeatherAPIs"
        function: "get_weather"
        parameters:
          - name: "city"
            type: "string"
            value: "Seattle"
    invocation_response_file: "responses/weather_seattle.json"
```

## Response Files

Response files can be in JSON or text format:

### JSON Response File

```json
{
  "statusCode": 200,
  "body": {
    "location": "Seattle",
    "temperature": 22,
    "condition": "Sunny",
    "humidity": 65,
    "wind_speed": 15
  }
}
```

### Text Response File

```txt
Weather information for Seattle: 22°C, Sunny, 65% humidity, 15 km/h wind speed.
```

## Parameter Matching

The framework performs exact matching on:

- **actionGroup**: The action group name
- **apiPath**: The API path (for API invocations)
- **httpMethod**: The HTTP method (for API invocations)
- **function**: The function name (for function invocations)
- **parameters**: Parameter names and values must match exactly

## Validation

The framework validates that:

1. **Expected invocations occur**: All defined expected invocations must be found in the agent's trace
2. **No unexpected invocations**: Any invocations not defined in the test will cause the test to fail
3. **Parameter matching**: All parameters must match exactly (name and value)

## Error Handling

If validation fails, the test will fail with one of these results:

- `RETURN_CONTROL_VALIDATION_FAILED`: Expected invocations not found or unexpected invocations detected
- Detailed error messages explaining what went wrong

## Examples

### Weather Agent Example

See the complete example in `samples/return_control/return_control.yml` for a full weather agent test with return control.

### Mixed Steps Example

```yaml
tests:
  mixed_test:
    steps:
      - "Start the conversation"
      - step: "Ask for weather information"
        expected_invocation:
          apiInvocationInput:
            actionGroup: "WeatherAPIs"
            apiPath: "/get-weather"
            httpMethod: "GET"
            parameters:
              - name: "location"
                type: "string"
                value: "Seattle"
          invocation_response_file: "responses/weather.json"
      - "Continue the conversation"
    expected_results:
      - "The agent provides weather information"
```

## Best Practices

1. **Use descriptive step names**: Make your step descriptions clear and actionable
2. **Organize response files**: Keep response files in a dedicated directory structure
3. **Test parameter variations**: Create multiple test cases with different parameter values
4. **Validate response content**: Ensure your mock responses are realistic and complete

## Limitations

- Currently supports Bedrock agents only
- Requires trace data to be enabled (`enableTrace: true`)
- Parameter matching is exact (no wildcards or patterns)
- Response files must be accessible from the test execution directory
