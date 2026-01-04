
from libraries.ContextTracker import context_tracker
from libraries.GenAIRescuer import GenAIRescuer
from robot.libraries.BuiltIn import BuiltIn
import re


class ExecutionListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self):
        self.depth = 0

    def start_test(self, name, attributes):
        context_tracker.set_test_name(name)
        self.depth = 0

    def start_keyword(self, name, attributes):
        self.depth += 1

    def end_keyword(self, name, attributes):
        # We only care about actual keywords, not control structures if possible, 
        # but 'Keyword' type covers most.
        if attributes['status'] == 'PASS':
            # Format: "KeywordName (Arg1, Arg2)"
            args = attributes.get('args', [])
            
            resolved_args = []
            rescuer = GenAIRescuer() 
            
            # Logic to resolve locator if it's a "Smart" keyword
            # Expected Smart Args: [page_name, element_name, ...]
            if name.startswith("GenAIRescuer.") or "Smart " in name:
                try:
                    if len(args) >= 2:
                        # 1. Resolve variables in arguments (e.g. ${PAGE_NAME} -> 'dynamic_page')
                        safe_args = [BuiltIn().replace_variables(a) for a in args]
                        
                        page = safe_args[0]
                        elem = safe_args[1]
                        
                        # Attempt to resolve locator
                        loc_data = rescuer.load_locator(page, elem)
                        if loc_data:
                            l_type = loc_data.get('type')
                            l_val = loc_data.get('value')
                            # specific format: "Smart Input Text (id:my-id, text_value)"
                            # We replace page, elem with valid locator
                            resolved_locator = f"{l_type}:{l_val}"
                            
                            # Reconstruct args: [resolved_locator, *rest]
                            # We skip page/elem and add the rest
                            rest_args = safe_args[2:]
                            resolved_args = [resolved_locator] + rest_args
                except:
                    pass # Fallback to original args
            
            if not resolved_args:
                resolved_args = args

            # Truncate long args to avoid bloating context
            args_str = ", ".join([str(a)[:50] for a in resolved_args])
            formatted_name = f"{name} ({args_str})" if args else name
            
            context_tracker.add_keyword(formatted_name)
            
            # If depth was 1, it was a top-level step
            if self.depth == 1:
                context_tracker.add_step(formatted_name)
        
        self.depth -= 1
