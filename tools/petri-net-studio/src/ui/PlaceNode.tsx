/**
 * Place node: a circle showing the live token count, name below (design §7).
 * One target handle (left) + one source handle (right) serve all arc directions.
 */

import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { StudioFlowNode } from "./flow.js";

export function PlaceNode({ data }: NodeProps<StudioFlowNode>) {
  return (
    <div className="place-node" title={data.name}>
      <Handle type="target" position={Position.Left} />
      <div className="place-circle">
        <span className="place-tokens">{data.tokens}</span>
      </div>
      <div className="node-name">{data.name}</div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
