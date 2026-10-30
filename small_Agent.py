import json
from abc import ABC, abstractmethod


class MemoryStrategy(ABC):
    @abstractmethod
    def select(self, messages): 
        ...

class WindowMemory(MemoryStrategy):
    def __init__(self, size=10):
        self.size = size
    def select(self, messages):
        return messages[-self.size:]

class Memory:                                  
    def __init__(self, strategy):
        self._messages = []
        self.strategy = strategy
    def add(self, role, content):
        self._messages.append({"role": role, "content": content})
    def get(self):
        return self.strategy.select(self._messages)


class ToolRegistry:
    def __init__(self):
        self._tools = {}
    def register(self, name=None):
        def decorator(func):
            self._tools[name or func.__name__] = func
            return func
        return decorator
    def run(self, name, **kwargs):
        return self._tools[name](**kwargs)

registry = ToolRegistry()

@registry.register()
def add(a: int, b: int):
    return a + b


class GeminiLLM:
    def __init__(self, replies):
        self._replies = iter(replies)
    def generate(self, messages):
        return next(self._replies)


class Agent:
    def __init__(self, llm, memory, registry, max_steps=5):
        self.llm = llm
        self.memory = memory
        self.registry = registry
        self.max_steps = max_steps

    def run(self, task):
        self.memory.add("user", task)
        for _ in range(self.max_steps):          
            data = json.loads(self.llm.generate(self.memory.get()))
            if "final" in data:
                return data["final"]
            result = self.registry.run(data["tool"], **data["args"])
            self.memory.add("tool", str(result))
        return "high level"

llm = GeminiLLM([
    '{"tool": "add", "args": {"a": 2, "b": 3}}',
    '{"final": "Answer: 5"}',
])

agent = Agent(llm, Memory(WindowMemory(10)), registry)
print(agent.run("2 Plus sign 3 "))      