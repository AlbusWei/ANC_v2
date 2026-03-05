import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";

const RUNNER_REL = "processes/control/trigger-event-runtime/scripts/trigger_event_runtime_runner.py";
const ROUTING_POLICY_REL = "runtime_data/private-assets/evolution/event-routing-policy.json";
const ESCALATION_POLICY_REL = "runtime_data/private-assets/evolution/event-escalation-policy.json";
const DEDUPE_LEDGER_REL = "runtime_data/evolution/hooks/dedupe_ledger.json";
const ESCALATION_COUNTER_REL = "runtime_data/evolution/hooks/escalation_counter.json";
const HOOK_LOG_REL = "runtime_data/evolution/hooks/logs/lifecycle-event-bridge.jsonl";

async function exists(targetPath) {
  try {
    await fs.access(targetPath);
    return true;
  } catch {
    return false;
  }
}

function asPosix(relPath) {
  return relPath.split(path.sep).join("/");
}

function toIso(raw) {
  if (typeof raw === "string" && raw.trim()) {
    const stamp = new Date(raw);
    if (!Number.isNaN(stamp.getTime())) {
      return stamp.toISOString();
    }
  }
  return new Date().toISOString();
}

function nowBucket(isoTs) {
  return isoTs.slice(0, 16).replace(/[-:]/g, "");
}

function envBool(name, fallback) {
  const raw = process.env[name];
  if (raw == null) {
    return fallback;
  }
  const normalized = String(raw).trim().toLowerCase();
  if (["1", "true", "yes", "on"].includes(normalized)) {
    return true;
  }
  if (["0", "false", "no", "off"].includes(normalized)) {
    return false;
  }
  return fallback;
}

function eventMapping(event) {
  const type = String(event?.type || "").trim();
  const action = String(event?.action || "").trim();

  if (type === "agent" && action === "bootstrap") {
    return {
      eventName: "platform.agent.bootstrap",
      module: "runtime-monitor",
      severity: "info",
    };
  }
  if (type === "command" && action === "new") {
    return {
      eventName: "platform.command.new",
      module: "runtime-monitor",
      severity: "info",
    };
  }
  if (type === "command" && action === "reset") {
    return {
      eventName: "platform.command.reset",
      module: "runtime-monitor",
      severity: "warning",
    };
  }
  if (type === "command" && action === "stop") {
    return {
      eventName: "platform.command.stop",
      module: "runtime-monitor",
      severity: "warning",
    };
  }
  if (type === "gateway" && action === "startup") {
    return {
      eventName: "platform.gateway.startup",
      module: "runtime-monitor",
      severity: "info",
    };
  }
  return null;
}

async function findRepoRoot(startDir) {
  let cursor = path.resolve(startDir);
  for (;;) {
    const gitPath = path.join(cursor, ".git");
    if (await exists(gitPath)) {
      return cursor;
    }
    const parent = path.dirname(cursor);
    if (parent === cursor) {
      return "";
    }
    cursor = parent;
  }
}

async function appendLog(repoRoot, payload) {
  const logPath = path.join(repoRoot, HOOK_LOG_REL);
  await fs.mkdir(path.dirname(logPath), { recursive: true });
  await fs.appendFile(logPath, `${JSON.stringify(payload)}\n`, "utf-8");
}

async function writeJson(targetPath, payload) {
  await fs.mkdir(path.dirname(targetPath), { recursive: true });
  await fs.writeFile(targetPath, `${JSON.stringify(payload, null, 2)}\n`, "utf-8");
}

function buildIngressPayload({ event, mapped, eventId, eventTime, evidenceRef }) {
  const sourceTag = String(event?.context?.commandSource || event?.type || "platform-hook").trim() || "platform-hook";
  const sender = String(event?.context?.senderId || "openclaw-hook").trim() || "openclaw-hook";
  const bucket = nowBucket(eventTime);
  const sessionKey = String(event?.sessionKey || "agent:main:main").trim() || "agent:main:main";
  // Default to active dispatch so matched events can advance instances; allow env override for safe rollback.
  const dispatchOpenclaw = envBool("ANC_LIFECYCLE_BRIDGE_DISPATCH_OPENCLAW", true);

  return {
    event_id: eventId,
    event_name: mapped.eventName,
    module: mapped.module,
    severity: mapped.severity,
    event_time: eventTime,
    entity_type: "skill",
    entity_id: "sys.bpm.process-instance-manager",
    from_status: "review",
    to_status: "active",
    transition_evidence_ref: evidenceRef,
    evidence_ref: evidenceRef,
    trigger_source: "platform-hook",
    emitted_by: sender,
    owner_agent_id: "owner",
    source_instance_id: sessionKey,
    window_bucket: bucket,
    canonical_event: mapped.eventName,
    hold_duration_minutes: 0,
    event_routing_policy_ref: ROUTING_POLICY_REL,
    event_escalation_policy_ref: ESCALATION_POLICY_REL,
    dedupe_ledger_ref: DEDUPE_LEDGER_REL,
    escalation_counter_ref: ESCALATION_COUNTER_REL,
    dispatch_openclaw: dispatchOpenclaw,
    reset_openclaw_session: dispatchOpenclaw,
    strict_session_match: dispatchOpenclaw,
    dispatch_openclaw_bin: "openclaw",
    dispatch_openclaw_stall_threshold_seconds: 900,
    dispatch_openclaw_probe_interval_seconds: 30,
    trace: {
      hook_name: "lifecycle-event-bridge",
      bridge_model: "platform-raw",
      openclaw_event_type: String(event?.type || ""),
      openclaw_event_action: String(event?.action || ""),
      command_source: sourceTag,
      session_key: sessionKey,
    },
  };
}

function shouldSkipEvent(event) {
  const type = String(event?.type || "").trim();
  const action = String(event?.action || "").trim();
  const sourceTag = String(event?.context?.commandSource || "").trim().toLowerCase();
  const sessionKey = String(event?.sessionKey || "").trim();

  if (type === "agent" && action === "bootstrap") {
    const managedSession =
      sessionKey.startsWith("agent:admin:") ||
      sessionKey.startsWith("agent:bpm:") ||
      sessionKey.includes(":cron:") ||
      sessionKey.includes(":subagent:");
    const internalSource = sourceTag === "agent" || sourceTag === "cron" || sourceTag === "heartbeat";
    if (managedSession || internalSource) {
      return { skip: true, reason: "internal_bootstrap_filtered" };
    }
  }

  return { skip: false, reason: "" };
}

function spawnRuntimeRunner(repoRoot, runId, inputRel, outputRel, evidenceRel) {
  const cmdArgs = [
    RUNNER_REL,
    "--input",
    inputRel,
    "--output",
    outputRel,
    "--evidence-dir",
    evidenceRel,
    "--run-id",
    runId,
  ];
  const child = spawn("python3", cmdArgs, {
    cwd: repoRoot,
    detached: true,
    stdio: "ignore",
  });
  child.unref();
}

async function resolveRepoRoot(event) {
  const candidates = [];
  if (typeof event?.context?.workspaceDir === "string" && event.context.workspaceDir.trim()) {
    candidates.push(event.context.workspaceDir.trim());
  }
  const cfgRepoRoot = event?.context?.cfg?.agents?.defaults?.repoRoot;
  if (typeof cfgRepoRoot === "string" && cfgRepoRoot.trim()) {
    candidates.push(cfgRepoRoot.trim());
  }
  candidates.push(process.cwd());

  for (const candidate of candidates) {
    const repo = await findRepoRoot(candidate);
    if (repo) {
      return repo;
    }
  }
  return "";
}

export default async function lifecycleEventBridge(event) {
  try {
    const mapped = eventMapping(event);
    if (!mapped) {
      return;
    }

    const repoRoot = await resolveRepoRoot(event);
    if (!repoRoot) {
      return;
    }

    const skipDecision = shouldSkipEvent(event);
    if (skipDecision.skip) {
      await appendLog(repoRoot, {
        ts: new Date().toISOString(),
        status: "skip",
        reason: skipDecision.reason,
        hook: "lifecycle-event-bridge",
        event_type: String(event?.type || ""),
        event_action: String(event?.action || ""),
        session_key: String(event?.sessionKey || ""),
      });
      return;
    }

    const runnerPath = path.join(repoRoot, RUNNER_REL);
    if (!(await exists(runnerPath))) {
      await appendLog(repoRoot, {
        ts: new Date().toISOString(),
        status: "skip",
        reason: "runner_missing",
        runnerPath,
        hook: "lifecycle-event-bridge",
      });
      return;
    }

    const timestamp = toIso(event?.timestamp);
    const rand = Math.random().toString(36).slice(2, 8);
    const eventNameTag = mapped.eventName.replace(/\./g, "-");
    const runId = `hook-${eventNameTag}-${Date.now()}-${rand}`;
    const hookRoot = path.join(repoRoot, "runtime_data/evolution/hooks");
    const ingressPath = path.join(hookRoot, "ingress", `${runId}.json`);
    const dispatchMetaPath = path.join(hookRoot, "dispatch", `${runId}.json`);
    const evidenceAbsDir = path.join(repoRoot, "runtime_data/execution/evidence/m5-self-evolution/hook-bridge", runId);
    const evidenceAbsPath = path.join(evidenceAbsDir, "hook_event_evidence.json");

    const eventId = `${runId}-evt`;
    const evidenceRel = asPosix(path.relative(repoRoot, evidenceAbsPath));
    const ingressPayload = buildIngressPayload({
      event,
      mapped,
      eventId,
      eventTime: timestamp,
      evidenceRef: evidenceRel,
    });

    await writeJson(evidenceAbsPath, {
      timestamp,
      hook_name: "lifecycle-event-bridge",
      run_id: runId,
      mapped_event: mapped,
      source_event: {
        type: String(event?.type || ""),
        action: String(event?.action || ""),
        sessionKey: String(event?.sessionKey || ""),
        commandSource: String(event?.context?.commandSource || ""),
        senderId: String(event?.context?.senderId || ""),
      },
      ingress_ref: asPosix(path.relative(repoRoot, ingressPath)),
    });
    await writeJson(ingressPath, ingressPayload);

    const runtimeOutputAbs = path.join(evidenceAbsDir, "runtime_output.json");
    const inputRel = asPosix(path.relative(repoRoot, ingressPath));
    const outputRel = asPosix(path.relative(repoRoot, runtimeOutputAbs));
    const evidenceDirRel = asPosix(path.relative(repoRoot, evidenceAbsDir));

    await writeJson(dispatchMetaPath, {
      timestamp,
      hook_name: "lifecycle-event-bridge",
      run_id: runId,
      ingress_ref: inputRel,
      runtime_output_ref: outputRel,
      evidence_ref: evidenceRel,
      status: "queued",
    });

    spawnRuntimeRunner(repoRoot, runId, inputRel, outputRel, evidenceDirRel);
    await appendLog(repoRoot, {
      ts: new Date().toISOString(),
      status: "queued",
      hook: "lifecycle-event-bridge",
      run_id: runId,
      event_id: eventId,
      event_name: mapped.eventName,
      runtime_output_ref: outputRel,
    });
  } catch (error) {
    try {
      const repoRoot = await resolveRepoRoot(event);
      if (repoRoot) {
        await appendLog(repoRoot, {
          ts: new Date().toISOString(),
          status: "error",
          hook: "lifecycle-event-bridge",
          error: error instanceof Error ? error.message : String(error),
        });
      }
    } catch {
      // fail-closed: 钩子内部异常仅吞掉，不外抛影响其他 hook。
    }
  }
}
