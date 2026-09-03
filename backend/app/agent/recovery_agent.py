"""Recovery agent using Gemini 3.6 Flash for AI-powered payment recovery."""

import json
from google import genai
from google.genai import types
from flask import current_app
from app import db
from app.models.recovery_case import RecoveryCase
from app.models.agent_decision import AgentDecision
from app.agent.prompts import get_system_prompt
from app.agent.tool_registry import get_tool_definitions
from app.agent.tools import dispatch_tool
from app.utils.logging import get_logger

logger = get_logger('recovery_agent')


class RecoveryAgent:
    """AI agent for payment recovery analysis using Gemini 3.6 Flash."""

    def __init__(self):
        """Initialize Gemini 3.6 Flash client with API key from config."""
        self.api_key = current_app.config.get('GEMINI_API_KEY', '')
        self.client = None
        self.model_name = 'gemini-3.6-flash'

        if self.api_key:
            logger.info("GEMINI_API_KEY FOUND")
            logger.info(f"GEMINI_API_KEY length: {len(self.api_key)}")
            logger.info("Initializing Gemini 3.6 Flash client...")
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Gemini 3.6 Flash client initialized successfully")
                logger.info(f"Model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}", exc_info=True)
                self.client = None
        else:
            logger.error("GEMINI_API_KEY NOT FOUND - will use ML fallback only")
            self.client = None

    def analyze(self, recovery_case_id: int) -> dict:
        """Analyze a recovery case and generate AI-powered recommendations."""
        logger.info(f"Analyzing recovery case {recovery_case_id}")

        case = RecoveryCase.query.get(recovery_case_id)
        if not case:
            return {'error': 'Recovery case not found'}

        payment = case.payment
        customer = payment.customer if payment else None

        if not payment or not customer:
            return {'error': 'Payment or customer not found'}

        # Prepare analysis context
        user_message = f"""
Analyze this failed payment for recovery:

Payment ID: {payment.id}
Amount: ₹{payment.amount / 100:.2f}
Failure Code: {payment.failure_code}
Failure Reason: {payment.failure_reason}
Attempt Number: {payment.attempt_number}

Customer: {customer.name}
Email: {customer.email}
Total Transactions: {customer.total_transactions}
Successful Transactions: {customer.successful_transactions}
Success Rate: {customer.success_rate:.1%}
Lifetime Value: ₹{customer.lifetime_value / 100:.2f}

Use the available tools to gather information and provide a recovery recommendation.
Return your analysis as JSON matching the required decision structure.
"""

        try:
            # Run AI analysis
            response = self._run_agentic_loop(user_message, payment, customer)

            # Store the decision
            self._store_decision(recovery_case_id, response, payment)

            return response

        except Exception as e:
            logger.error(f"Agent analysis failed: {e}", exc_info=True)
            return {'error': str(e), 'status': 'failed'}

    def _run_agentic_loop(self, user_message: str, payment, customer) -> dict:
        """Execute Gemini 3.6 Flash agentic loop with function calling.

        Handles Gemini's strict message turn ordering:
        User → Assistant (may have tool calls) → User (tool results) → ...
        """
        logger.info("========== GEMINI AGENT START ==========")

        if not self.client:
            logger.error("GEMINI_FAILURE_FALLBACK: Gemini client not initialized")
            logger.error("Reason: No API key configured")
            return self._fallback_analysis(payment, customer)

        try:
            system_prompt = get_system_prompt()
            tool_definitions = get_tool_definitions()
            tool_calls_history = []

            # Convert tool definitions to Gemini format
            gemini_tools = self._convert_tools_to_gemini_format(tool_definitions)

            # Initialize conversation with system prompt and user message
            full_message = f"{system_prompt}\n\n{user_message}"

            max_iterations = 8
            iteration = 0
            # Build message history as we go
            contents = full_message  # First iteration uses plain string

            while iteration < max_iterations:
                iteration += 1
                logger.info(f"Agent iteration {iteration}")
                logger.info("GEMINI REQUEST START")
                logger.info(f"Model: {self.model_name}")
                logger.info("Calling Gemini API...")

                try:
                    # Call Gemini 3.6 Flash API
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            tools=gemini_tools,
                            temperature=0.3,
                        ),
                    )
                    logger.info("GEMINI RESPONSE RECEIVED")
                    logger.info(f"Response has {len(response.candidates) if response.candidates else 0} candidates")

                except Exception as e:
                    logger.error(f"GEMINI_FAILURE_FALLBACK: Gemini API call failed")
                    logger.error(f"Exception: {type(e).__name__}: {e}", exc_info=True)
                    return self._fallback_analysis(payment, customer)

                # Process response
                if not response.candidates:
                    logger.error("GEMINI_FAILURE_FALLBACK: No candidates in response")
                    break

                candidate = response.candidates[0]
                finish_reason = candidate.finish_reason
                logger.info(f"Finish reason: {finish_reason}")

                # Extract text and function calls from response
                has_function_calls = False
                final_text = ""
                tool_results_parts = []

                for part in candidate.content.parts:
                    # Handle text parts
                    if hasattr(part, 'text') and part.text:
                        final_text += part.text
                        logger.debug(f"Text part received: {part.text[:100]}...")

                    # Handle function calls
                    if hasattr(part, 'function_call') and part.function_call:
                        has_function_calls = True
                        fc = part.function_call
                        tool_name = fc.name
                        tool_args = dict(fc.args) if fc.args else {}

                        logger.info(f"Gemini requested tool: {tool_name}")
                        logger.info(f"Tool arguments: {json.dumps(tool_args, default=str)}")

                        # Execute the tool
                        try:
                            result = dispatch_tool(tool_name, tool_args)
                            logger.info(f"Tool {tool_name} executed successfully")

                            # Store in history
                            tool_calls_history.append({
                                'tool': tool_name,
                                'input': tool_args,
                                'output': result,
                            })

                            # Create function response part
                            part = types.Part.from_function_response(
                                name=tool_name,
                                response=result,
                            )
                            tool_results_parts.append(part)

                        except Exception as e:
                            logger.error(f"Tool execution failed: {tool_name} - {e}")
                            # Still create response even on error
                            part = types.Part.from_function_response(
                                name=tool_name,
                                response={"error": str(e)},
                            )
                            tool_results_parts.append(part)

                # Handle function calls: rebuild contents for next turn
                if has_function_calls and tool_results_parts:
                    logger.info(f"Processing {len(tool_results_parts)} tool results...")

                    # Build message list for next iteration
                    # Current contents is either a string (iteration 1) or list (iteration 2+)
                    if isinstance(contents, str):
                        # First iteration: convert to proper message list
                        messages = [
                            types.Content(role="user", parts=[types.Part(text=contents)]),
                            candidate.content,
                        ]
                    else:
                        # Subsequent iterations: contents is already a list
                        messages = contents + [candidate.content]

                    # Add tool results as user turn
                    tool_result_message = types.Content(
                        role="user",
                        parts=tool_results_parts,
                    )
                    messages.append(tool_result_message)

                    # Next iteration uses the message list
                    contents = messages
                    continue

                # If final response with text (no function calls)
                if finish_reason == types.FinishReason.STOP and final_text and not has_function_calls:
                    logger.info("GEMINI_SUCCESS: Gemini final response received")
                    logger.info(f"Response preview: {final_text[:300]}...")

                    # Clean up markdown if present
                    final_text = self._clean_json_response(final_text)

                    return {
                        'status': 'completed',
                        'decision_json': final_text,
                        'tool_calls': tool_calls_history,
                    }

                # If STOP but no text and no function calls, break
                if finish_reason == types.FinishReason.STOP and not final_text and not has_function_calls:
                    logger.warning("Gemini returned STOP with no text and no function calls")
                    break

            logger.error("GEMINI_FAILURE_FALLBACK: Max iterations reached without final response")
            return {
                'status': 'max_iterations',
                'tool_calls': tool_calls_history,
                'error': 'Max iterations reached',
            }

        except Exception as e:
            logger.error(f"GEMINI_FAILURE_FALLBACK: Agentic loop failed")
            logger.error(f"Exception: {type(e).__name__}: {e}", exc_info=True)
            return self._fallback_analysis(payment, customer)

    def _convert_tools_to_gemini_format(self, tool_definitions: list) -> list:
        """Convert tool definitions to Gemini function calling format."""
        gemini_tools = []

        for tool in tool_definitions:
            # Gemini expects tools in this format
            gemini_tool = types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name=tool.get('name'),
                        description=tool.get('description', ''),
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                prop_name: types.Schema(
                                    type=self._convert_json_type_to_schema_type(prop.get('type')),
                                    description=prop.get('description', ''),
                                    enum=prop.get('enum', None),
                                )
                                for prop_name, prop in tool.get('parameters', {}).get('properties', {}).items()
                            },
                            required=tool.get('parameters', {}).get('required', []),
                        ),
                    )
                ]
            )
            gemini_tools.append(gemini_tool)

        return gemini_tools

    def _convert_json_type_to_schema_type(self, json_type: str) -> types.Type:
        """Convert JSON schema type to Gemini Schema type."""
        type_map = {
            'string': types.Type.STRING,
            'integer': types.Type.INTEGER,
            'number': types.Type.NUMBER,
            'boolean': types.Type.BOOLEAN,
            'object': types.Type.OBJECT,
            'array': types.Type.ARRAY,
        }
        return type_map.get(json_type, types.Type.STRING)

    def _clean_json_response(self, text: str) -> str:
        """Remove markdown code blocks from response if present."""
        if text.startswith('```'):
            # Remove opening fence
            text = text.split('```', 1)[1]
            if text.startswith('json'):
                text = text[4:]
            # Remove closing fence
            if '```' in text:
                text = text.rsplit('```', 1)[0]
        return text.strip()

    def _store_decision(self, recovery_case_id: int, response: dict, payment) -> None:
        """Store the AI decision in the database."""
        try:
            decision_json = response.get('decision_json', '{}')

            # Parse the decision
            decision_data = json.loads(decision_json)

            # Create AgentDecision record
            decision = AgentDecision(
                recovery_case_id=recovery_case_id,
                diagnosis=decision_data.get('diagnosis', {}).get('failure_category'),
                reasoning_summary=decision_data.get('reasoning_summary', ''),
                confidence=decision_data.get('confidence_overall', 0),
                recommended_action=decision_data.get('recommendation', {}).get('action'),
                tool_calls=response.get('tool_calls', []),
            )
            db.session.add(decision)

            # Update RecoveryCase
            case = RecoveryCase.query.get(recovery_case_id)
            if case:
                case.status = 'ACTION_PENDING'
                case.diagnosis = decision_data.get('diagnosis', {}).get('root_cause')
                case.confidence = decision_data.get('confidence_overall')
                case.recommended_action = decision_data.get('recommendation', {}).get('action')
                case.recovery_probability = decision_data.get('recommendation', {}).get('recovery_probability')
                case.expected_recovery = int(
                    payment.amount * (decision_data.get('recommendation', {}).get('recovery_probability', 0.5))
                )

            db.session.commit()
            logger.info("Decision stored successfully")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse decision JSON: {e}")
            logger.error(f"Raw response: {response.get('decision_json')}")
        except Exception as e:
            logger.error(f"Failed to store decision: {e}")
            db.session.rollback()

    def _fallback_analysis(self, payment, customer) -> dict:
        """Fallback to ML predictor when Gemini is unavailable."""
        logger.warning("========== GEMINI_FAILURE_FALLBACK: Using ML predictor ==========")
        logger.warning("Gemini 3.6 Flash not available - falling back to XGBoost ML model")

        from app.utils.helpers import classify_failure
        from app.ml.predictor import get_predictor

        predictor = get_predictor()

        # Build feature dict
        feature_dict = {
            'amount': payment.amount,
            'currency': 'INR',
            'payment_method': payment.payment_method,
            'failure_code': payment.failure_code or 'unknown',
            'failure_category': classify_failure(payment.failure_code),
            'attempt_number': payment.attempt_number,
            'customer_total_transactions': customer.total_transactions,
            'customer_successful_transactions': customer.successful_transactions,
            'customer_failed_transactions': customer.failed_transactions,
            'customer_success_rate': customer.success_rate,
            'customer_lifetime_value': customer.lifetime_value,
            'is_subscription': 0,
            'hours_since_failure': 1.0,
        }

        # Get prediction
        prediction = predictor.predict(feature_dict)
        category = classify_failure(payment.failure_code, payment.attempt_number)

        # Build decision
        decision = {
            'diagnosis': {
                'failure_category': category,
                'root_cause': payment.failure_reason or 'Unknown',
                'confidence': 0.65,
            },
            'recommendation': {
                'action': 'RETRY' if prediction['probability'] > 0.65 else 'ESCALATE',
                'reasoning': f'ML recovery probability: {prediction["probability"]:.1%}',
                'evidence': [
                    f'Customer success rate: {customer.success_rate:.1%}',
                    f'ML prediction: {prediction["probability"]:.1%}',
                ],
                'recovery_probability': prediction['probability'],
            },
            'confidence_overall': 0.65,
            'reasoning_summary': 'ML fallback analysis (Gemini 3.6 Flash unavailable)',
        }

        return {
            'status': 'fallback',
            'decision_json': json.dumps(decision),
            'tool_calls': [],
        }
