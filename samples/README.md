# Agent Evaluation Samples

This directory contains sample configurations and code examples for using the Agent Evaluation framework.

## ReturnControl Examples

### Basic Usage

- `return_control_example.py` - Standalone Python script demonstrating returnControl event handling
- `test_plan_templates/bedrock_agent_target/return_control_example.yml` - Basic YAML test plan for returnControl scenarios
- `test_plan_templates/bedrock_agent_target/return_control_with_hooks.yml` - Advanced YAML test plan using hooks

### Hook Examples

- `hooks/return_control_handler.py` - Example hook implementation for handling returnControl events programmatically

## Running the Examples

### Python Script Example

```bash
# Set your AWS credentials and agent details
export BEDROCK_AGENT_ID="your-agent-id"
export BEDROCK_AGENT_ALIAS_ID="your-alias-id"
export AWS_REGION="us-east-1"

# Run the example script
python samples/return_control_example.py
```

### YAML Test Plan Examples

```bash
# Run basic returnControl tests
agenteval run samples/test_plan_templates/bedrock_agent_target/return_control_example.yml

# Run advanced returnControl tests with hooks
agenteval run samples/test_plan_templates/bedrock_agent_target/return_control_with_hooks.yml
```

## Customizing the Examples

1. **Update Agent IDs**: Replace `BEDROCK_AGENT_ID` and `BEDROCK_AGENT_ALIAS_ID` with your actual agent details
2. **Modify Test Scenarios**: Adjust the test steps and expected results to match your agent's capabilities
3. **Customize Hooks**: Modify the hook implementations to handle your specific action groups and parameters

## Key Features Demonstrated

- **Automatic returnControl Detection**: The target automatically detects and exposes returnControl events
- **Programmatic Handling**: Use hooks to provide structured responses to returnControl events
- **Multi-turn Testing**: Test complex workflows that require multiple conversation turns
- **YAML Integration**: Seamlessly integrate returnControl testing with standard YAML configurations
