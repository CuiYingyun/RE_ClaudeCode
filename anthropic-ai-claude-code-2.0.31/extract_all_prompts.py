#!/usr/bin/env python3
"""
Complete Prompt Extractor for Claude Code CLI
Extracts ALL prompts from the obfuscated cli.js file
"""

import re
import json

def extract_prompts():
    with open('cli.js', 'r', encoding='utf-8') as f:
        content = f.read()

    results = {}

    # 1. Extract all "You are" variants
    you_are_patterns = [
        r'"(You are Claude Code[^"]{100,5000})"',
        r'"(You are an agent for Claude Code[^"]{50,2000})"',
        r'"(You are a Claude agent[^"]{50,1000})"',
        r'"(You are a code reviewer[^"]{50,1000})"',
    ]

    for pattern in you_are_patterns:
        matches = re.findall(pattern, content, re.DOTALL)
        for m in matches:
            key = f"YOU_ARE_{len(results)}"
            results[key] = m

    # 2. Extract IMPORTANT security policy
    important_pattern = r'"(IMPORTANT: Assist with authorized[^"]{200,1000})"'
    matches = re.findall(important_pattern, content, re.DOTALL)
    if matches:
        results["SECURITY_POLICY"] = matches[0]

    # 3. Extract tool descriptions - look for specific tools
    tool_patterns = {
        "READ_TOOL": r'"(Reads a file from the local filesystem[^"]{300,3000})"',
        "BASH_TOOL": r'"(Executes a given bash command[^"]{300,4000})"',
        "EDIT_TOOL": r'"(Performs exact string replacements[^"]{200,2000})"',
        "GREP_TOOL": r'"(A powerful search tool built on ripgrep[^"]{200,2000})"',
        "GLOB_TOOL": r'"(Fast file pattern matching tool[^"]{100,1500})"',
        "WRITE_TOOL": r'"(Writes a file to the local filesystem[^"]{200,1500})"',
        "TODO_TOOL": r'"(Use this tool[^"]{200,3000}todo[^"]{0,1000})"',
        "TASK_TOOL": r'"(Launch a new agent[^"]{400,3500})"',
        "WEBFETCH_TOOL": r'"(Fetches content from a specified URL[^"]{200,2000})"',
        "WEBSEARCH_TOOL": r'"(Allows Claude to search the web[^"]{200,2000})"',
    }

    for name, pattern in tool_patterns.items():
        matches = re.findall(pattern, content, re.DOTALL)
        if matches:
            results[name] = matches[0]

    # 4. Extract system-reminder patterns
    reminder_pattern = r'<system-reminder>([^<]{100,2000})</system-reminder>'
    matches = re.findall(reminder_pattern, content, re.DOTALL)
    for i, m in enumerate(matches):
        results[f"SYSTEM_REMINDER_{i+1}"] = m.strip()

    # 5. Extract "Usage notes" sections
    usage_pattern = r'"(Usage notes?:[^"]{100,2000})"'
    matches = re.findall(usage_pattern, content)
    for i, m in enumerate(matches):
        results[f"USAGE_NOTES_{i+1}"] = m

    # 6. Extract DO NOT / NEVER / ALWAYS instructions
    instruction_patterns = [
        r'"([^"]{50,1000}DO NOT[^"]{50,1000})"',
        r'"([^"]{50,1000}NEVER[^"]{50,1000})"',
        r'"([^"]{50,1000}ALWAYS[^"]{50,1000})"',
    ]

    instruction_count = 0
    for pattern in instruction_patterns:
        matches = re.findall(pattern, content)
        for m in matches:
            if len(m) > 100:  # Only keep substantial instructions
                results[f"INSTRUCTION_{instruction_count+1}"] = m
                instruction_count += 1

    return results

def format_output(results):
    output = []
    output.append("="*80)
    output.append("CLAUDE CODE CLI - COMPLETE PROMPT EXTRACTION")
    output.append("="*80)
    output.append(f"\nTotal prompts extracted: {len(results)}\n")

    for key, value in sorted(results.items()):
        output.append("\n" + "="*80)
        output.append(f"[{key}] ({len(value)} characters)")
        output.append("="*80)
        output.append(value)
        output.append("="*80)

    return "\n".join(output)

if __name__ == "__main__":
    print("Extracting prompts from cli.js...")
    prompts = extract_prompts()
    output = format_output(prompts)

    with open('ALL_PROMPTS_EXTRACTED.txt', 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"✓ Extracted {len(prompts)} prompts")
    print("✓ Saved to ALL_PROMPTS_EXTRACTED.txt")

    # Also save as JSON for programmatic access
    with open('ALL_PROMPTS_EXTRACTED.json', 'w', encoding='utf-8') as f:
        json.dump(prompts, f, indent=2, ensure_ascii=False)

    print("✓ Saved to ALL_PROMPTS_EXTRACTED.json")
