import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ReactFlowProvider } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import "../styles.css";
import { Dashboard } from "./Dashboard.js";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ReactFlowProvider>
      <Dashboard />
    </ReactFlowProvider>
  </StrictMode>,
);
