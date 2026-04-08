---
title: AI Code Review Assistant
emoji: [BOT]
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# AI Code Review Assistant

## Overview
AI Code Review Assistant is a production-grade **AI Code Review Environment** designed for the OpenEnv Hackathon. It simulates a real-world software engineering workflow where an AI agent acts as a Senior Reviewer, analyzing Pull Requests for bugs, performance bottlenecks, and security vulnerabilities.

Unlike static analysis tools, AI Code Review Assistant provides a dynamic, stateful environment where the agent can interact with the repository, read multiple files, and provide structured feedback that is graded against deterministic truth.

## Features
- **Real-World Simulations**: Three tasks ranging from basic division-by-zero errors to complex IDOR and SQL Injection vulnerabilities.
- **Fractional Reward System**: Rewards are not binary. Agents earn partial credit for finding issues and requesting changes appropriately.
- **Futuristic Dashboard**: A high-performance Streamlit UI for human-in-the-loop evaluation and visualization.
- **OpenEnv Compliant**: Fully implements the `reset`, `step`, and `state` interface with typed Pydantic models.

## Action and Observation Spaces

### Observation Space
The agent receives a rich state including:
- `pr_details`: Context about what the developer intended to do.
- `files`: A list of file paths available in the PR.
- `current_file_content`: The raw source code of the file currently being inspected.
- `comments`: A record of all reviews posted so far.
- `code_output`: (Optional) The result of dry-running the code in the sandbox.

### Action Space
The agent can execute following commands:
1. `read_file`: Pulls the content of a specific file into the observation.
2. `add_comment`: Places a technical review comment on a specific line.
3. `request_changes`: Submits the final review and finishes the task.

## Multi-Dimensional Reward Policy (RL-Ready)
Our environment employs a multi-dimensional, continuous reward signal rather than a sparse, binary pass/fail score. This provides the agent with granular "partial progress" feedback throughout the review lifecycle, perfectly aligning with OpenEnv constraints (normalized strictly between 0.0 and 1.0).

The reward is structured into three critical checkpoints:
1. **Execution Signal (The Base Mechanic)**: The agent first attempts to run the code in a sandbox. Success yields a positive baseline reward (+2.0); crashes or infinite loops trigger an immediate penalty (-2.0).
2. **Policy Quality (The Intelligent Signal)**: An RL Meta-Critic parses the agent's code review. A rank (0-10) is converted into a weighted quality reward (up to +5.0), rewarding depth and technical accuracy.
3. **Security Constraints (The Guardrail)**: Deterministic security checks on the agent's output. Verifying safety yields a bonus (+2.0), while missing critical vulnerabilities (e.g., IDOR) triggers a severe safety penalty (-3.0).

**Normalization**: The raw accumulated score (ranging from -5.0 to +9.0) is mathematically normalized into the strict [0.0, 1.0] limit required by the Phase 2 Automated Grader.

## Setup & Evaluation

### Prerequisites
- Python 3.10+
- OpenAI API Key (or HF Token for proxy usage)

### Local Launch
Run the environment and dashboard:
```cmd
run.bat
```

### Agent Evaluation
Run the autonomous agent against the environment:
```cmd
set API_BASE_URL=...
set API_KEY=...
set MODEL_NAME=...
python inference.py
```

## OpenEnv Validation
This project passes all Phase 1 and Phase 2 checks:
- [x] HF Space Deployment
- [x] OpenEnv Spec Compliance
- [x] Docker Build Success
- [x] LLM Proxy Usage (Verified via LiteLLM)
- [x] Non-Binary Reward Range [0.0 - 1.0]
