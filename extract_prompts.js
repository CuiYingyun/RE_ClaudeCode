const fs = require('fs');

const content = fs.readFileSync('./cli.js', 'utf-8');

// Extract all strings between quotes
const strings = [];
const regex = /"([^"]{50,5000})"/g;
let match;

while ((match = regex.exec(content)) !== null) {
  strings.push(match[1]);
}

// Filter for prompts
const prompts = strings.filter(s => {
  const lower = s.toLowerCase();
  return (
    s.includes('You are') ||
    s.includes('IMPORTANT:') ||
    s.includes('Usage notes') ||
    s.includes('tool') && s.length > 200 ||
    s.includes('description') && s.length > 200 ||
    s.includes('Execute') ||
    s.includes('Reads') ||
    s.includes('Writes') ||
    s.includes('Performs') ||
    s.includes('agent') && s.length > 200 ||
    s.includes('When to') ||
    s.includes('DO NOT') ||
    s.includes('NEVER') ||
    s.includes('ALWAYS')
  );
});

// Output
console.log(`Total strings found: ${strings.length}`);
console.log(`Prompts found: ${prompts.length}`);
console.log('\n=== PROMPTS ===\n');

prompts.forEach((p, i) => {
  console.log(`\n[${i+1}] LENGTH: ${p.length}`);
  console.log('---');
  console.log(p);
  console.log('---');
});
