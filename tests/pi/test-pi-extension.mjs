import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import test from 'node:test';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(__dirname, '../..');
const packageJsonPath = resolve(repoRoot, 'package.json');
const extensionPath = resolve(repoRoot, '.pi/extensions/superpowers.ts');

async function readPackageJson() {
  return JSON.parse(await readFile(packageJsonPath, 'utf8'));
}

async function loadExtension() {
  const handlers = new Map();
  const pi = {
    on(event, handler) {
      if (!handlers.has(event)) handlers.set(event, []);
      handlers.get(event).push(handler);
    },
  };
  const mod = await import(pathToFileURL(extensionPath).href + `?cachebust=${Date.now()}-${Math.random()}`);
  mod.default(pi);
  return { handlers };
}

function firstHandler(handlers, event) {
  const eventHandlers = handlers.get(event) ?? [];
  assert.equal(eventHandlers.length, 1, `expected one ${event} handler`);
  return eventHandlers[0];
}

function textOf(message) {
  if (typeof message.content === 'string') return message.content;
  return message.content
    .filter((part) => part.type === 'text')
    .map((part) => part.text)
    .join('\n');
}

test('package.json declares a pi package with skills and extension resources', async () => {
  const pkg = await readPackageJson();

  assert.equal(pkg.name, 'superpowers');
  assert.ok(pkg.keywords.includes('pi-package'));
  assert.deepEqual(pkg.pi.skills, ['./skills']);
  assert.deepEqual(pkg.pi.extensions, ['./.pi/extensions/superpowers.ts']);
});

test('extension registers lifecycle hooks without pre-compaction injection', async () => {
  const { handlers } = await loadExtension();

  for (const event of ['resources_discover', 'session_start', 'session_compact', 'context', 'agent_end']) {
    assert.equal((handlers.get(event) ?? []).length, 1, `missing ${event} handler`);
  }
  assert.equal((handlers.get('session_before_compact') ?? []).length, 0);
});

test('extension source does not read or embed the using-superpowers skill body', async () => {
  const source = await readFile(extensionPath, 'utf8');

  assert.doesNotMatch(source, /readFileSync|readFile\(/);
  assert.doesNotMatch(source, /using-superpowers[\\/]+SKILL\.md/);
  assert.doesNotMatch(source, /stripFrontmatter|cachedBootstrap/);
});

test('resources_discover contributes the bundled skills directory', async () => {
  const { handlers } = await loadExtension();
  const discover = firstHandler(handlers, 'resources_discover');

  const result = await discover({ type: 'resources_discover', cwd: repoRoot, reason: 'startup' }, {});

  assert.deepEqual(result.skillPaths, [resolve(repoRoot, 'skills')]);
});

test('startup context injects the Pi tool mapping as one user message until agent_end', async () => {
  const { handlers } = await loadExtension();
  const sessionStart = firstHandler(handlers, 'session_start');
  const context = firstHandler(handlers, 'context');
  const agentEnd = firstHandler(handlers, 'agent_end');

  await sessionStart({ type: 'session_start', reason: 'startup' }, {});

  const originalMessages = [
    { role: 'user', content: [{ type: 'text', text: 'Let us make a react todo list' }], timestamp: 1 },
  ];
  const result = await context({ type: 'context', messages: originalMessages }, {});

  assert.equal(result.messages.length, 2);
  assert.equal(result.messages[0].role, 'user');
  const injectedText = textOf(result.messages[0]);
  assert.match(injectedText, /Pi Tool Mapping/);
  for (const tool of [
    'Agent',
    'get_subagent_result',
    'steer_subagent',
    'TaskCreate',
    'TaskList',
    'TaskGet',
    'TaskUpdate',
    'TaskExecute',
    'TaskOutput',
    'TaskStop',
  ]) {
    assert.match(injectedText, new RegExp(`\\b${tool}\\b`), `mapping documents ${tool}`);
  }
  assert.doesNotMatch(injectedText, /If you think there is even a 1% chance/);
  assert.doesNotMatch(injectedText, /## The Rule/);
  assert.doesNotMatch(injectedText, /## Red Flags/);
  assert.equal(result.messages[1], originalMessages[0]);

  const alreadyInjected = await context({ type: 'context', messages: result.messages }, {});
  assert.equal(alreadyInjected, undefined, 'mapping should not duplicate when already present');

  await agentEnd({ type: 'agent_end', messages: [] }, {});
  const afterEnd = await context({ type: 'context', messages: originalMessages }, {});
  assert.equal(afterEnd, undefined, 'startup mapping should clear after agent_end');
});

test('session_compact injects mapping after compaction summaries, not before compaction', async () => {
  const { handlers } = await loadExtension();
  const sessionCompact = firstHandler(handlers, 'session_compact');
  const context = firstHandler(handlers, 'context');

  await sessionCompact({ type: 'session_compact', compactionEntry: {}, fromExtension: false }, {});

  const summary = { role: 'compactionSummary', summary: 'Prior work summary', tokensBefore: 123, timestamp: 1 };
  const user = { role: 'user', content: [{ type: 'text', text: 'Continue' }], timestamp: 2 };
  const result = await context({ type: 'context', messages: [summary, user] }, {});

  assert.equal(result.messages.length, 3);
  assert.equal(result.messages[0], summary);
  assert.equal(result.messages[1].role, 'user');
  assert.match(textOf(result.messages[1]), /Pi Tool Mapping/);
  assert.equal(result.messages[2], user);
});

test('using-superpowers is marked user-invoked only', async () => {
  const skill = await readFile(resolve(repoRoot, 'skills/using-superpowers/SKILL.md'), 'utf8');

  assert.match(skill, /^---\n[\s\S]*?disable-model-invocation: true[\s\S]*?---/);
});

test('mapping tells the agent not to self-invoke using-superpowers', async () => {
  const source = await readFile(extensionPath, 'utf8');

  assert.match(source, /user-invoked only/);
  assert.match(source, /\/skill:using-superpowers/);
});
