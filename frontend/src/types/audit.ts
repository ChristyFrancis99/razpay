import type { Decision } from "./risk";

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  actor: string;
  actorRole: string;
  action: string;
  entity: string;
  previousDecision: Decision | null;
  newDecision: Decision | null;
  reason: string;
}
