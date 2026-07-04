import { createHashRouter } from "react-router-dom"
import App from "./App.jsx"
import Home from "../pages/Home.jsx"
import Journey from "../pages/Journey.jsx"
import Architecture from "../pages/Architecture.jsx"
import VibeCode from "../pages/VibeCode.jsx"
import PmLog from "../pages/PmLog.jsx"

export const router = createHashRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <Home /> },
      { path: "journey", element: <Journey /> },
      { path: "architecture", element: <Architecture /> },
      { path: "vibe-code", element: <VibeCode /> },
      { path: "pm-log", element: <PmLog /> },
    ],
  },
])
