"""Recovery agent using Gemini for tool-calling."""

import json
import google.generativeai as genai
from flask import current_app
from app import db
from app.models.recovery_case import RecoveryCase
from app.models.agent_decision import AgentDecision
from app.agent.prompts import get_system_prompt
from app.agent.tool_registry import get_tool_definitions
from app.agent.tools import dispatch_tool
from app.agent.schemas import AgentDecisionResponse
from app.utils.logging import get_logger

logger = get_logger('recovery_agent')


class RecoveryAgent:
    """AI agent for payment recovery analysis and decision-making."""

    def __init__(self):
        self.api_key = current_app.config.get('GEMINI_API_KEY', '')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            logger.warning("GEMINI_API_KEY not configured. Agent will use fallback mode.")
            self.model = None

    def analyze(self, recovery_case_id: int) -> dict:
        """Analyze a recovery case and generate recommendations."""
        case = RecoveryCase.query.get(recovery_case_id)
        if not case:
            return {'error': 'Recovery case not found'}

        payment = case.payment
        customer = payment.customer if payment else None

        if not payment or not customer:
            return {'error': 'Payment or customer not found'}

        # Prepare initial context
        user_message = f"""
Analyze this failed payment for recovery:

Payment ID: {payment.id}
Amount: ₹{payment.amount / 100:.2f}
Failure Code: {payment.failure_code}
Customer: {customer.name}
Success Rate: {customer.success_rate:.1%}
Lifetime Value: ₹{customer.lifetime_value / 100:.2f}

Use your tools to gather information and make a recovery recommendation.
"""

        try:
            response = self._run_agentic_loop(user_message, payment, customer)

            # Store decision
            try:
                decision_data = json.loads(response.get('decision_json', '{}'))
                decision = AgentDecision(
                    recovery_case_id=recovery_case_id,
                    diagnosis=decision_data.get('diagnosis', {}).get('failure_category'),
                    reasoning_summary=decision_data.get('reasoning_summary', ''),
                    confidence=decision_data.get('confidence_overall', 0),
                    recommended_action=decision_data.get('recommendation', {}).get('action'),
                    tool_calls=response.get('tool_calls', []),
                )
                db.session.add(decision)

                case.status = 'ACTION_PENDING'
                case.diagnosis = decision_data.get('diagnosis', {}).get('root_cause')
                case.confidence = decision_data.get('confidence_overall')
                case.recommended_action = decision_data.get('recommendation', {}).get('action')
                case.recovery_probability = decision_data.get('recommendation', {}).get('recovery_probability')
                case.expected_recovery = int(payment.amount * (decision_data.get('recommendation', {}).get('recovery_probability', 0.5)))

                db.session.commit()
            except Exception as e:
                logger.error(f"Failed to store decision: {e}")

            return response

        except Exception as e:
            logger.error(f"Agent analysis failed: {e}")
            return {'error': str(e)}

    def _run_agentic_loop(self, user_message: str, payment, customer) -> dict:
        """Run the Gemini agentic loop."""
        if not self.model:
            return self._fallback_analysis(payment, customer)

        messages = []
        tool_calls_history = []

        # Initial request
        messages.append({
            'role': 'user',
            'content': user_message,
        })

        system_prompt = get_system_prompt()
        tool_definitions = get_tool_definitions()

        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Agent iteration {iteration}")

            # Call Gemini
            response = self.model.generate_content(
                messages,
                system_instruction=system_prompt,
                tools=[{'function_declarations': tool_definitions}],
            )

            # Check if done
            if response.candidates[0].finish_reason.name == 'STOP':
                # Final response
                final_text = response.candidates[0].content.parts[0].text
                logger.info(f"Agent final response: {final_text[:200]}...")

                return {
                    'status': 'completed',
                    'decision_json': final_text,
                    'tool_calls': tool_calls_history,
                }

            # Process function calls
            function_calls = response.candidates[0].content.parts[0].function_calls
            if not function_calls:
                break

            # Dispatch tools
            tool_results = []
            for fc in function_calls:
                tool_name = fc.name
                tool_input = dict(fc.args)
                logger.info(f"Tool call: {tool_name}({tool_input})")

                result = dispatch_tool(tool_name, tool_input)
                tool_calls_history.append({
                    'tool': tool_name,
                    'input': tool_input,
                    'output': result,
                })

                tool_results.append({
                    'function_name': tool_name,
                    'output': json.dumps(result),
                })

            # Add assistant response and tool results to messages
            messages.append({'role': 'model', 'content': response.candidates[0].content})
            messages.append({
                'role': 'user',
                'content': [{'function_response': {'name': tr['function_name'], 'response': json.loads(tr['output'])}} for tr in tool_results]
            })

        return {
            'status': 'max_iterations',
            'tool_calls': tool_calls_history,
            'error': 'Max iterations reached without final response',
        }

    def _fallback_analysis(self, payment, customer) -> dict:
        """Fallback analysis when Gemini is not configured."""
        logger.warning("Using fallback analysis (Gemini not configured)")

        from app.utils.helpers import classify_failure
        predictor = __import__('app.ml.predictor', fromlist=['get_predictor']).get_predictor()

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

        prediction = predictor.predict(feature_dict)
        category = classify_failure(payment.failure_code, payment.attempt_number)

        decision = {
            'diagnosis': {
                'failure_category': category,
                'root_cause': payment.failure_reason or 'Unknown',
                'confidence': 0.65,
            },
            'recommendation': {
                'action': 'RETRY' if prediction['probability'] > 0.65 else 'ESCALATE',
                'reasoning': f'Recovery probability: {prediction["probability"]:.1%}',
                'evidence': [
                    f'Customer success rate: {customer.success_rate:.1%}',
                    f'ML prediction: {prediction["probability"]:.1%}',
                ],
                'recovery_probability': prediction['probability'],
            },
            'confidence_overall': 0.65,
            'reasoning_summary': 'Fallback analysis using ML predictor',
        }

        return {
            'status': 'fallback',
            'decision_json': json.dumps(decision),
            'tool_calls': [],
        }
