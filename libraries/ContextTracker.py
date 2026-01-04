
class ContextTracker:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ContextTracker, cls).__new__(cls)
            cls._instance.reset()
        return cls._instance

    def reset(self):
        self.current_test_name = "Unknown Test"
        self.recent_keywords = [] # Stores all completed keywords
        self.recent_steps = []    # Stores top-level keywords (Test Steps)
        self.max_history = 10     # Keep a buffer, user wants 3 but we store more just in case

    def set_test_name(self, name):
        self.current_test_name = name

    def add_keyword(self, name):
        self.recent_keywords.append(name)
        if len(self.recent_keywords) > self.max_history:
            self.recent_keywords.pop(0)

    def add_step(self, name):
        self.recent_steps.append(name)
        if len(self.recent_steps) > self.max_history:
            self.recent_steps.pop(0)

    def get_context(self):
        return {
            "test_name": self.current_test_name,
            "last_keywords": self.recent_keywords[-3:],
            "last_steps": self.recent_steps[-3:]
        }

# Global instance
context_tracker = ContextTracker()
