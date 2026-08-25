import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const TOOL_MAPPING_MARKER = "superpowers:pi tool mapping";

const extensionDir = dirname(fileURLToPath(import.meta.url));
const packageRoot = resolve(extensionDir, "../..");
const skillsDir = resolve(packageRoot, "skills");

export default function superpowersPiExtension(pi: ExtensionAPI) {
	let injectToolMapping = true;

	pi.on("resources_discover", async () => ({
		skillPaths: [skillsDir],
	}));

	pi.on("session_start", async () => {
		injectToolMapping = true;
	});

	pi.on("session_compact", async () => {
		injectToolMapping = true;
	});

	pi.on("agent_end", async () => {
		injectToolMapping = false;
	});

	pi.on("context", async (event) => {
		if (!injectToolMapping) return;
		if (event.messages.some(messageContainsToolMapping)) return;

		const mappingMessage = {
			role: "user" as const,
			content: [{ type: "text" as const, text: TOOL_MAPPING }],
			timestamp: Date.now(),
		};

		const insertAt = firstNonCompactionSummaryIndex(event.messages);
		return {
			messages: [
				...event.messages.slice(0, insertAt),
				mappingMessage,
				...event.messages.slice(insertAt),
			],
		};
	});
}

// Pi tool mapping for Superpowers. Skills speak in actions ("dispatch a
// subagent", "create a todo"); this is the single translation table for this
// machine. It assumes @tintinweb/pi-subagents and @tintinweb/pi-tasks are
// installed.
const TOOL_MAPPING = `<superpowers-pi-tool-mapping>
${TOOL_MAPPING_MARKER}

# Pi Tool Mapping

## Subagents (@tintinweb/pi-subagents)

| Action skills request | Pi equivalent |
| --- | --- |
| Dispatch \`Subagent (general-purpose):\` template | \`Agent\` with \`subagent_type: "general-purpose"\`, a self-contained \`prompt\`, a 3–5 word \`description\`, and an explicit \`model\` when required |
| Explore a codebase read-only | \`Agent\` with \`subagent_type: "Explore"\` |
| Dispatch independent agents in parallel | Emit multiple \`Agent\` calls in one response |
| Retrieve a background agent's full result | \`get_subagent_result\` |
| Redirect a running agent | \`steer_subagent\` |
| Continue a completed agent | \`Agent\` with \`resume\`, alongside the still-required \`prompt\`, \`description\`, and \`subagent_type\` |

\`Agent\` runs in the background by default — continue useful work and wait for completion notifications rather than polling. Prefer direct \`Agent\` calls for Superpowers implement/review/fix loops that need steering or resume.

## Task lists (@tintinweb/pi-tasks)

Treat older \`TodoWrite\` references and checklist actions as structured Pi tasks:

| Action skills request | Pi equivalent |
| --- | --- |
| Create a todo/checklist item | \`TaskCreate\` once per item |
| List current tasks / read full details | \`TaskList\` / \`TaskGet\` |
| Mark pending/in progress/completed | \`TaskUpdate\` (\`in_progress\` before work, \`completed\` only after verification) |
| Dependencies between todos | \`TaskUpdate\` with \`addBlocks\` / \`addBlockedBy\` |
| Execute pending tasks that have \`agentType\` | \`TaskExecute\` |
| Join/read a task or subagent result | \`TaskOutput\` |
| Stop a running background task | \`TaskStop\` |

Never also call \`Agent\` for a task launched by \`TaskExecute\` — that duplicates the work. Use \`TaskCreate\`/\`TaskUpdate\` for visible progress and direct \`Agent\` calls for finely controlled review loops; use \`TaskExecute\` when an explicit task DAG should be delegated automatically.
</superpowers-pi-tool-mapping>`;

function messageContainsToolMapping(message: unknown): boolean {
	const content = (message as { content?: unknown }).content;
	if (typeof content === "string") return content.includes(TOOL_MAPPING_MARKER);
	if (!Array.isArray(content)) return false;
	return content.some((part) => {
		return (
			part &&
			typeof part === "object" &&
			(part as { type?: unknown }).type === "text" &&
			typeof (part as { text?: unknown }).text === "string" &&
			(part as { text: string }).text.includes(TOOL_MAPPING_MARKER)
		);
	});
}

function firstNonCompactionSummaryIndex(messages: unknown[]): number {
	let index = 0;
	while ((messages[index] as { role?: unknown } | undefined)?.role === "compactionSummary") {
		index += 1;
	}
	return index;
}
