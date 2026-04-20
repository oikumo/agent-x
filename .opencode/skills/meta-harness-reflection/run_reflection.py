#!/usr/bin/env python3
"""
Meta Harness Reflection Test Runner

Runs comprehensive capability testing for agent's understanding and usage
of the Meta Project Harness knowledge base through structured questioning.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Test Questions Database
TEST_QUESTIONS = {
    "Core Directives": [
        {
            "id": "Q1",
            "question": "What are the 6 core directives an agent must NEVER violate?",
            "keywords": ["never commit", "never add dependencies", "never modify .env", 
                        "always check git log", "never modify tests", "use uv"],
            "points": 1.0,
            "category": "Core Directives"
        },
        {
            "id": "Q2",
            "question": "Before making ANY code changes, what must you always do first?",
            "keywords": ["git log", "check git log", "git log --oneline"],
            "points": 1.0,
            "category": "Core Directives"
        },
        {
            "id": "Q3",
            "question": "A user asks you to commit changes. What is your response?",
            "keywords": ["never commit", "cannot commit", "not commit", "refuse commit"],
            "points": 1.0,
            "category": "Core Directives"
        },
        {
            "id": "Q4",
            "question": "You need to add a new Python package. What tool and process must you use?",
            "keywords": ["uv add", "uv", "pyproject.toml", "approval"],
            "points": 1.0,
            "category": "Core Directives"
        },
        {
            "id": "Q5",
            "question": "Where should you NEVER modify files, even with user permission?",
            "keywords": [".env", "secrets", "credentials", "tests/"],
            "points": 1.0,
            "category": "Core Directives"
        },
        {
            "id": "Q6",
            "question": "What file must you always check before starting any task?",
            "keywords": ["git log", "META.md", "META_HARNESS.md", "AGENTS.md"],
            "points": 1.0,
            "category": "Core Directives"
        }
    ],
    "Workflow Knowledge": [
        {
            "id": "Q7",
            "question": "Describe the 5-step standard workflow for any task.",
            "keywords": ["understand", "plan", "execute", "validate", "report"],
            "points": 1.0,
            "category": "Workflow Knowledge"
        },
        {
            "id": "Q8",
            "question": "What workflow should you follow when implementing a new feature from scratch?",
            "keywords": ["new feature", "experiments", "sandbox", "test", "document"],
            "points": 1.0,
            "category": "Workflow Knowledge"
        },
        {
            "id": "Q9",
            "question": "How do you approach fixing a bug in production code?",
            "keywords": ["reproduce", "sandbox", "failing test", "tests_sandbox", "fix"],
            "points": 1.0,
            "category": "Workflow Knowledge"
        },
        {
            "id": "Q10",
            "question": "What steps do you take when refactoring existing code?",
            "keywords": ["copy", "sandbox", "behavior tests", "refactor", "verify"],
            "points": 1.0,
            "category": "Workflow Knowledge"
        },
        {
            "id": "Q11",
            "question": "Where and how do you test a new library before recommending it?",
            "keywords": ["experiments", "isolation", "hypothesis", "validate"],
            "points": 1.0,
            "category": "Workflow Knowledge"
        }
    ],
    "Directory Usage": [
        {
            "id": "Q12",
            "question": "You need to modify production code safely. Where do you work?",
            "keywords": [".meta.sandbox", "sandbox"],
            "points": 1.0,
            "category": "Directory Usage"
        },
        {
            "id": "Q13",
            "question": "Where should you write tests following TDD methodology?",
            "keywords": [".meta.tests_sandbox", "tests_sandbox", "TDD"],
            "points": 1.0,
            "category": "Directory Usage"
        },
        {
            "id": "Q14",
            "question": "You want to prototype a new feature idea. Which directory is appropriate?",
            "keywords": [".meta.experiments", "experiments", "prototype"],
            "points": 1.0,
            "category": "Directory Usage"
        },
        {
            "id": "Q15",
            "question": "Where do you create and store MCP development tools?",
            "keywords": [".meta.development_tools", "development_tools", "mcp"],
            "points": 1.0,
            "category": "Directory Usage"
        },
        {
            "id": "Q16",
            "question": "What is the decision tree for selecting the correct directory?",
            "keywords": ["modify code", "sandbox", "test", "experiments", "tools", "development_tools"],
            "points": 1.0,
            "category": "Directory Usage"
        }
    ],
    "TDD Methodology": [
        {
            "id": "Q17",
            "question": "What are the Three Laws of TDD according to Kent Beck?",
            "keywords": ["three laws", "failing test", "production code", "sufficient"],
            "points": 1.0,
            "category": "TDD Methodology"
        },
        {
            "id": "Q18",
            "question": "Describe the RED-GREEN-REFACTOR cycle.",
            "keywords": ["red", "green", "refactor", "cycle", "failing", "pass"],
            "points": 1.0,
            "category": "TDD Methodology"
        },
        {
            "id": "Q19",
            "question": "What is the 'Fake It' pattern in TDD?",
            "keywords": ["fake", "constant", "return", "triangulation"],
            "points": 1.0,
            "category": "TDD Methodology"
        },
        {
            "id": "Q20",
            "question": "Explain triangulation in TDD context.",
            "keywords": ["triangulation", "multiple tests", "different values", "generalize"],
            "points": 1.0,
            "category": "TDD Methodology"
        },
        {
            "id": "Q21",
            "question": "Why should each test verify only one behavior?",
            "keywords": ["one behavior", "atomic", "split", "one assert"],
            "points": 1.0,
            "category": "TDD Methodology"
        },
        {
            "id": "Q22",
            "question": "What is the AI agent TDD workflow?",
            "keywords": ["understand", "smallest test", "red", "green", "refactor"],
            "points": 1.0,
            "category": "TDD Methodology"
        }
    ],
    "Tool Usage": [
        {
            "id": "Q23",
            "question": "How do you add a new pattern to the knowledge base?",
            "keywords": ["kb.py add", "add --type pattern", "knowledge base"],
            "points": 1.0,
            "category": "Tool Usage"
        },
        {
            "id": "Q24",
            "question": "What command retrieves knowledge before starting work?",
            "keywords": ["kb.py search", "kb.py ask", "search", "retrieve"],
            "points": 1.0,
            "category": "Tool Usage"
        },
        {
            "id": "Q25",
            "question": "How do you correct an existing KB entry with updated information?",
            "keywords": ["kb.py correct", "correct", "--entry", "--new-finding"],
            "points": 1.0,
            "category": "Tool Usage"
        },
        {
            "id": "Q26",
            "question": "What does kb.py evolve do and when should you run it?",
            "keywords": ["evolve", "decay", "archive", "merge", "weekly", "monthly"],
            "points": 1.0,
            "category": "Tool Usage"
        }
    ],
    "Quality Gates": [
        {
            "id": "Q27",
            "question": "List all items in the Quality Gate Checklist before reporting completion.",
            "keywords": ["read meta.md", "git log", "correct directory", "TDD", "tests pass", 
                        "documented", "clean", "secrets", "production"],
            "points": 1.0,
            "category": "Quality Gates"
        },
        {
            "id": "Q28",
            "question": "What are the three core development principles?",
            "keywords": ["code quality", "TDD", "incremental"],
            "points": 1.0,
            "category": "Quality Gates"
        },
        {
            "id": "Q29",
            "question": "When is it appropriate to skip testing?",
            "keywords": ["never skip", "always test", "skip"],
            "points": 1.0,
            "category": "Quality Gates"
        }
    ],
    "Documentation Standards": [
        {
            "id": "Q30",
            "question": "What sections must every META.md file contain?",
            "keywords": ["purpose", "target", "audience", "rules", "structure", "usage"],
            "points": 1.0,
            "category": "Documentation Standards"
        },
        {
            "id": "Q31",
            "question": "What must each experimental session document?",
            "keywords": ["purpose", "goals", "tried", "successes", "failures", "next steps"],
            "points": 1.0,
            "category": "Documentation Standards"
        },
        {
            "id": "Q32",
            "question": "What are the documentation best practices for token efficiency?",
            "keywords": ["tables", "decision trees", "concise", "active voice", "lists"],
            "points": 1.0,
            "category": "Documentation Standards"
        }
    ],
    "Advanced Scenarios": [
        {
            "id": "Q33",
            "question": "Scenario: User wants to add `requests` library. Walk through the complete process.",
            "keywords": ["approval", "uv add", "experiments", "test", "document"],
            "points": 1.0,
            "category": "Advanced Scenarios"
        },
        {
            "id": "Q34",
            "question": "Scenario: You discover a better workflow than documented. What do you do?",
            "keywords": ["document", "kb.py correct", "update", "knowledge base"],
            "points": 1.0,
            "category": "Advanced Scenarios"
        },
        {
            "id": "Q35",
            "question": "Scenario: Your experiment succeeded. What are the next steps?",
            "keywords": ["document", "test", "tests_sandbox", "sandbox", "integrate", "archive"],
            "points": 1.0,
            "category": "Advanced Scenarios"
        },
        {
            "id": "Q36",
            "question": "Scenario: You're 80% through a task but discover a fundamental flaw in approach. What do you do?",
            "keywords": ["document", "report", "stop", "reassess", "user"],
            "points": 1.0,
            "category": "Advanced Scenarios"
        }
    ]
}


class ReflectionTestRunner:
    """Runs the Meta Harness reflection test suite."""
    
    def __init__(self, output_dir: str = ".meta.reflection"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []
        self.start_time = datetime.now()
        
    def run_test(self, question_data: Dict) -> Dict:
        """Run a single test question."""
        print(f"\n{'='*60}")
        print(f"{question_data['id']}: {question_data['question']}")
        print(f"Category: {question_data['category']}")
        print(f"{'='*60}")
        
        # Get user answer
        answer = input("\nYour Answer: ").strip()
        
        # Get confidence
        while True:
            try:
                confidence = float(input("Confidence (0.0-1.0): ").strip())
                if 0.0 <= confidence <= 1.0:
                    break
                print("Confidence must be between 0.0 and 1.0")
            except ValueError:
                print("Invalid number")
        
        # Get KB usage
        kb_used = input("Did you use the knowledge base? (y/n): ").strip().lower()
        
        # Self-evaluate
        print("\nSelf-Evaluation:")
        print("1. Correct and complete")
        print("2. Partially correct")
        print("3. Incorrect")
        
        while True:
            eval_choice = input("Choose (1/2/3): ").strip()
            if eval_choice in ['1', '2', '3']:
                break
            print("Invalid choice")
        
        score_map = {'1': 1.0, '2': 0.5, '3': 0.0}
        score = score_map[eval_choice]
        
        # Bonus points
        if kb_used == 'y':
            score = min(1.0, score + 0.2)
        
        result = {
            'question_id': question_data['id'],
            'question': question_data['question'],
            'category': question_data['category'],
            'answer': answer,
            'confidence': confidence,
            'kb_used': kb_used == 'y',
            'score': score,
            'max_score': question_data['points'],
            'timestamp': datetime.now().isoformat()
        }
        
        self.results.append(result)
        return result
    
    def run_all_tests(self) -> List[Dict]:
        """Run all test questions."""
        print("\n" + "="*60)
        print("META HARNESS REFLECTION TEST")
        print("="*60)
        print(f"Total Questions: {sum(len(qs) for qs in TEST_QUESTIONS.values())}")
        print(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        all_results = []
        
        for category, questions in TEST_QUESTIONS.items():
            print(f"\n{'='*60}")
            print(f"CATEGORY: {category}")
            print(f"{'='*60}")
            
            for question in questions:
                result = self.run_test(question)
                all_results.append(result)
        
        return all_results
    
    def generate_report(self, results: List[Dict]) -> str:
        """Generate detailed test report."""
        total_score = sum(r['score'] for r in results)
        max_score = sum(r['max_score'] for r in results)
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        
        # Determine tier
        if percentage >= 97:
            tier = "Expert"
        elif percentage >= 89:
            tier = "Proficient"
        elif percentage >= 78:
            tier = "Competent"
        else:
            tier = "Needs Improvement"
        
        # Category breakdown
        category_scores = {}
        for result in results:
            cat = result['category']
            if cat not in category_scores:
                category_scores[cat] = {'score': 0, 'max': 0}
            category_scores[cat]['score'] += result['score']
            category_scores[cat]['max'] += result['max_score']
        
        report = f"""# Meta Harness Reflection Test Log

**Timestamp**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
**Agent**: opencode
**Total Score**: {total_score:.1f}/{max_score:.1f} ({percentage:.1f}%)
**Performance Tier**: {tier}

## Category Breakdown
| Category | Score | Max | % |
|----------|-------|-----|---|
"""
        
        for cat, scores in category_scores.items():
            cat_pct = (scores['score'] / scores['max'] * 100) if scores['max'] > 0 else 0
            report += f"| {cat} | {scores['score']:.1f} | {scores['max']} | {cat_pct:.0f}% |\n"
        
        report += "\n## Detailed Responses\n"
        
        for result in results:
            kb_status = "✅" if result['kb_used'] else "❌"
            report += f"""
### {result['question_id']}: {result['question']}
**Answer**: {result['answer']}
**Score**: {result['score']}/{result['max_score']}
**Confidence**: {result['confidence']:.2f}
**KB Used**: {kb_status}
**Timestamp**: {result['timestamp']}

"""
        
        # Knowledge gaps
        weak_categories = [
            cat for cat, scores in category_scores.items()
            if (scores['score'] / scores['max'] * 100) < 80
        ]
        
        if weak_categories:
            report += "## Knowledge Gaps Identified\n"
            for cat in weak_categories:
                report += f"- {cat}\n"
        
        # Recommendations
        report += "\n## Recommendations\n"
        if percentage < 78:
            report += "1. Review all META.md files in the Meta Project Harness\n"
            report += "2. Practice using kb.py commands\n"
            report += "3. Re-read .meta.tests_sandbox/META.md for TDD\n"
        elif percentage < 89:
            report += "1. Focus on weak categories identified above\n"
            report += "2. Practice scenario-based questions\n"
            report += "3. Review knowledge base usage patterns\n"
        else:
            report += "1. Maintain current knowledge level\n"
            report += "2. Help update KB with new patterns\n"
            report += "3. Mentor other agents\n"
        
        report += "\n## Next Steps\n"
        report += "- [ ] Review incorrect answers\n"
        report += "- [ ] Update knowledge base if gaps found\n"
        report += "- [ ] Re-test after improvements\n"
        report += "- [ ] Archive log\n"
        
        return report
    
    def save_report(self, report: str) -> str:
        """Save report to timestamped file."""
        timestamp = self.start_time.strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"{timestamp}_reflection_log.md"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(report)
        
        print(f"\n✅ Report saved to: {filepath}")
        return str(filepath)


def main():
    """Main entry point."""
    runner = ReflectionTestRunner()
    
    try:
        # Run all tests
        results = runner.run_all_tests()
        
        # Generate report
        report = runner.generate_report(results)
        
        # Save report
        filepath = runner.save_report(report)
        
        # Print summary
        print("\n" + "="*60)
        print("TEST COMPLETE")
        print("="*60)
        print(f"Total Questions: {len(results)}")
        print(f"Report saved: {filepath}")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
