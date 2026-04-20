#!/usr/bin/env python3
"""
Meta Harness Reflection - Automated Test Runner

Runs automated capability testing using knowledge base search to validate answers.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Test Questions with Expected Answers
TEST_QUESTIONS = [
    {
        "id": "Q1",
        "question": "What are the 6 core directives an agent must NEVER violate?",
        "expected_keywords": ["never commit", "never add dependencies", "never modify .env", 
                             "always check git log", "never modify tests/", "use uv"],
        "category": "Core Directives",
        "points": 1.0
    },
    {
        "id": "Q2",
        "question": "Before making ANY code changes, what must you always do first?",
        "expected_keywords": ["check git log", "git log"],
        "category": "Core Directives",
        "points": 1.0
    },
    {
        "id": "Q3",
        "question": "A user asks you to commit changes. What is your response?",
        "expected_keywords": ["never commit", "cannot commit", "not commit"],
        "category": "Core Directives",
        "points": 1.0
    },
    {
        "id": "Q4",
        "question": "You need to add a new Python package. What tool and process must you use?",
        "expected_keywords": ["uv add", "uv", "pyproject.toml"],
        "category": "Core Directives",
        "points": 1.0
    },
    {
        "id": "Q5",
        "question": "Where should you NEVER modify files, even with user permission?",
        "expected_keywords": [".env", "secrets", "tests/"],
        "category": "Core Directives",
        "points": 1.0
    },
    {
        "id": "Q6",
        "question": "What file must you always check before starting any task?",
        "expected_keywords": ["git log", "META.md", "META_HARNESS.md", "AGENTS.md"],
        "category": "Core Directives",
        "points": 1.0
    },
    {
        "id": "Q7",
        "question": "Describe the 5-step standard workflow for any task.",
        "expected_keywords": ["understand", "plan", "execute", "validate", "report"],
        "category": "Workflow Knowledge",
        "points": 1.0
    },
    {
        "id": "Q8",
        "question": "What workflow should you follow when implementing a new feature from scratch?",
        "expected_keywords": ["experiments", "sandbox", "test", ".meta.experiments"],
        "category": "Workflow Knowledge",
        "points": 1.0
    },
    {
        "id": "Q9",
        "question": "How do you approach fixing a bug in production code?",
        "expected_keywords": ["reproduce", "sandbox", "test", ".meta.sandbox"],
        "category": "Workflow Knowledge",
        "points": 1.0
    },
    {
        "id": "Q10",
        "question": "What steps do you take when refactoring existing code?",
        "expected_keywords": ["copy", "sandbox", "behavior tests", "refactor"],
        "category": "Workflow Knowledge",
        "points": 1.0
    },
    {
        "id": "Q11",
        "question": "Where and how do you test a new library before recommending it?",
        "expected_keywords": ["experiments", "isolation", "hypothesis", ".meta.experiments"],
        "category": "Workflow Knowledge",
        "points": 1.0
    },
    {
        "id": "Q12",
        "question": "You need to modify production code safely. Where do you work?",
        "expected_keywords": [".meta.sandbox", "sandbox"],
        "category": "Directory Usage",
        "points": 1.0
    },
    {
        "id": "Q13",
        "question": "Where should you write tests following TDD methodology?",
        "expected_keywords": [".meta.tests_sandbox", "tests_sandbox"],
        "category": "Directory Usage",
        "points": 1.0
    },
    {
        "id": "Q14",
        "question": "You want to prototype a new feature idea. Which directory is appropriate?",
        "expected_keywords": [".meta.experiments", "experiments"],
        "category": "Directory Usage",
        "points": 1.0
    },
    {
        "id": "Q15",
        "question": "Where do you create and store MCP development tools?",
        "expected_keywords": [".meta.development_tools", "development_tools", "mcp"],
        "category": "Directory Usage",
        "points": 1.0
    },
    {
        "id": "Q16",
        "question": "What is the decision tree for selecting the correct directory?",
        "expected_keywords": ["modify code", "sandbox", "test", "experiments"],
        "category": "Directory Usage",
        "points": 1.0
    },
    {
        "id": "Q17",
        "question": "What are the Three Laws of TDD according to Kent Beck?",
        "expected_keywords": ["three laws", "failing test", "production code"],
        "category": "TDD Methodology",
        "points": 1.0
    },
    {
        "id": "Q18",
        "question": "Describe the RED-GREEN-REFACTOR cycle.",
        "expected_keywords": ["red", "green", "refactor", "failing", "pass"],
        "category": "TDD Methodology",
        "points": 1.0
    },
    {
        "id": "Q19",
        "question": "What is the 'Fake It' pattern in TDD?",
        "expected_keywords": ["fake", "constant", "return"],
        "category": "TDD Methodology",
        "points": 1.0
    },
    {
        "id": "Q20",
        "question": "Explain triangulation in TDD context.",
        "expected_keywords": ["triangulation", "multiple tests", "different values", "generalize"],
        "category": "TDD Methodology",
        "points": 1.0
    },
    {
        "id": "Q21",
        "question": "Why should each test verify only one behavior?",
        "expected_keywords": ["one behavior", "atomic", "split"],
        "category": "TDD Methodology",
        "points": 1.0
    },
    {
        "id": "Q22",
        "question": "What is the AI agent TDD workflow?",
        "expected_keywords": ["understand", "smallest test", "red", "green", "refactor"],
        "category": "TDD Methodology",
        "points": 1.0
    },
    {
        "id": "Q23",
        "question": "How do you add a new pattern to the knowledge base?",
        "expected_keywords": ["kb.py add", "add --type pattern"],
        "category": "Tool Usage",
        "points": 1.0
    },
    {
        "id": "Q24",
        "question": "What command retrieves knowledge before starting work?",
        "expected_keywords": ["kb.py search", "kb.py ask", "search"],
        "category": "Tool Usage",
        "points": 1.0
    },
    {
        "id": "Q25",
        "question": "How do you correct an existing KB entry with updated information?",
        "expected_keywords": ["kb.py correct", "correct", "--entry"],
        "category": "Tool Usage",
        "points": 1.0
    },
    {
        "id": "Q26",
        "question": "What does kb.py evolve do and when should you run it?",
        "expected_keywords": ["evolve", "decay", "archive", "merge", "weekly"],
        "category": "Tool Usage",
        "points": 1.0
    },
    {
        "id": "Q27",
        "question": "List all items in the Quality Gate Checklist before reporting completion.",
        "expected_keywords": ["read meta.md", "git log", "correct directory", "TDD", 
                             "tests pass", "documented", "clean"],
        "category": "Quality Gates",
        "points": 1.0
    },
    {
        "id": "Q28",
        "question": "What are the three core development principles?",
        "expected_keywords": ["code quality", "TDD", "incremental"],
        "category": "Quality Gates",
        "points": 1.0
    },
    {
        "id": "Q29",
        "question": "When is it appropriate to skip testing?",
        "expected_keywords": ["never skip", "always test"],
        "category": "Quality Gates",
        "points": 1.0
    },
    {
        "id": "Q30",
        "question": "What sections must every META.md file contain?",
        "expected_keywords": ["purpose", "target", "audience", "rules", "structure"],
        "category": "Documentation Standards",
        "points": 1.0
    },
    {
        "id": "Q31",
        "question": "What must each experimental session document?",
        "expected_keywords": ["purpose", "goals", "tried", "successes", "failures"],
        "category": "Documentation Standards",
        "points": 1.0
    },
    {
        "id": "Q32",
        "question": "What are the documentation best practices for token efficiency?",
        "expected_keywords": ["tables", "decision trees", "concise", "active voice"],
        "category": "Documentation Standards",
        "points": 1.0
    },
    {
        "id": "Q33",
        "question": "Scenario: User wants to add `requests` library. Walk through the complete process.",
        "expected_keywords": ["approval", "uv add", "experiments", "test"],
        "category": "Advanced Scenarios",
        "points": 1.0
    },
    {
        "id": "Q34",
        "question": "Scenario: You discover a better workflow than documented. What do you do?",
        "expected_keywords": ["document", "kb.py correct", "update", "knowledge base"],
        "category": "Advanced Scenarios",
        "points": 1.0
    },
    {
        "id": "Q35",
        "question": "Scenario: Your experiment succeeded. What are the next steps?",
        "expected_keywords": ["document", "test", "sandbox", "integrate"],
        "category": "Advanced Scenarios",
        "points": 1.0
    },
    {
        "id": "Q36",
        "question": "Scenario: You're 80% through a task but discover a fundamental flaw in approach. What do you do?",
        "expected_keywords": ["document", "report", "stop", "reassess"],
        "category": "Advanced Scenarios",
        "points": 1.0
    }
]


class AutomatedReflectionRunner:
    """Runs automated reflection tests using KB search."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.kb_path = self.project_root / ".meta.knowledge_base"
        self.output_dir = self.project_root / ".meta.reflection"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []
        self.start_time = datetime.now()
        
    def search_kb(self, query: str) -> str:
        """Search knowledge base for answer."""
        try:
            cmd = [
                "uv", "run", "python", 
                str(self.kb_path / "kb.py"),
                "search", query, "--top-k", "1"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.stdout
        except Exception as e:
            return f"Error: {e}"
    
    def evaluate_answer(self, answer: str, expected_keywords: List[str]) -> Tuple[float, List[str]]:
        """Evaluate answer against expected keywords."""
        answer_lower = answer.lower()
        matched = []
        
        for keyword in expected_keywords:
            if keyword.lower() in answer_lower:
                matched.append(keyword)
        
        match_ratio = len(matched) / len(expected_keywords) if expected_keywords else 0
        
        if match_ratio >= 0.8:
            score = 1.0
        elif match_ratio >= 0.5:
            score = 0.5
        else:
            score = 0.0
        
        return score, matched
    
    def run_question(self, question_data: Dict) -> Dict:
        """Run a single question."""
        print(f"\nTesting: {question_data['id']}")
        print(f"Question: {question_data['question']}")
        
        # Search KB for answer
        kb_answer = self.search_kb(question_data['question'])
        
        # Evaluate
        score, matched = self.evaluate_answer(kb_answer, question_data['expected_keywords'])
        
        result = {
            'question_id': question_data['id'],
            'question': question_data['question'],
            'category': question_data['category'],
            'kb_search_performed': True,
            'kb_answer': kb_answer[:200] + "..." if len(kb_answer) > 200 else kb_answer,
            'matched_keywords': matched,
            'expected_keywords': question_data['expected_keywords'],
            'score': score,
            'max_score': question_data['points'],
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"Score: {score}/{question_data['points']}")
        print(f"Matched keywords: {', '.join(matched) if matched else 'None'}")
        
        return result
    
    def run_all_tests(self) -> List[Dict]:
        """Run all test questions."""
        print("\n" + "="*60)
        print("META HARNESS REFLECTION TEST - AUTOMATED")
        print("="*60)
        print(f"Total Questions: {len(TEST_QUESTIONS)}")
        print(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        all_results = []
        
        for question in TEST_QUESTIONS:
            result = self.run_question(question)
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
        
        report = f"""# Meta Harness Reflection Test Log (Automated)

**Timestamp**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
**Agent**: opencode
**Test Type**: Automated KB Search
**Total Score**: {total_score:.1f}/{max_score:.1f} ({percentage:.1f}%)
**Performance Tier**: {tier}

## Category Breakdown
| Category | Score | Max | % |
|----------|-------|-----|---|
"""
        
        for cat, scores in category_scores.items():
            cat_pct = (scores['score'] / scores['max'] * 100) if scores['max'] > 0 else 0
            report += f"| {cat} | {scores['score']:.1f} | {scores['max']} | {cat_pct:.0f}% |\n"
        
        report += "\n## Detailed Results\n"
        
        for result in results:
            kb_status = "✅" if result['kb_search_performed'] else "❌"
            matched_str = ', '.join(result['matched_keywords']) if result['matched_keywords'] else 'None'
            
            report += f"""
### {result['question_id']}: {result['question']}
**Score**: {result['score']}/{result['max_score']}
**KB Search**: {kb_status}
**Matched Keywords**: {matched_str}
**Expected Keywords**: {', '.join(result['expected_keywords'][:3])}...
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
    project_root = Path(__file__).parent.parent.parent.parent
    runner = AutomatedReflectionRunner(project_root)
    
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
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
