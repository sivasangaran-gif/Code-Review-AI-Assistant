import sys
from server.app import frontend_step
from server.models import Action as ActionModel # Not needed for this test but for reference
from server.app import SandboxRequest

def test():
    print("Testing Sandbox Correct Python...")
    action = SandboxRequest(action_type="paste_code", code="print('Welcome to BugHunter AI!')", language="python")
    res = frontend_step(action)
    print(f"Reward: {res['reward']}")
    print(f"Issues: {res['issues']}")
    print(f"Impact: {res['impact']}")

    print("\n-------------------------------\n")
    print("Testing Sandbox Wrong Python...")
    action2 = SandboxRequest(action_type="paste_code", code="print('Welcome to BugHunter AI!')wee", language="python")
    res2 = frontend_step(action2)
    print(f"Reward: {res2['reward']}")
    print(f"Issues: {res2['issues']}")
    print(f"Impact: {res2['impact']}")

if __name__ == "__main__":
    test()
