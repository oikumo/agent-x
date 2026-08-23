/**
 * Transition node: a bar showing its name (design §7). In simulate mode an
 * enabled transition gets the distinct style (green border + shadow), a
 * disabled one is muted; clicking fires it (handled by App's onNodeClick).
 */

import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { StudioFlowNode } from "./flow.js";

export function TransitionNode({ data }: NodeProps<StudioFlowNode>) {
  const stateClass = data.simulate ? (data.enabled ? "enabled" : "disabled") : "edit";
  return (
    <div className={`transition-node ${stateClass}`} title={data.name}>
      <Handle type="target" position={Position.Left} />
      <div className="transition-bar" />
      <div className="node-name">{data.name}</div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
