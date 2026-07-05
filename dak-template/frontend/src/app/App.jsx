import { useState } from "react"
import { Outlet, useLocation, useNavigate } from "react-router-dom"
import { AppShell } from "@astryxdesign/core/AppShell"
import { SideNav, SideNavSection, SideNavItem, SideNavHeading } from "@astryxdesign/core/SideNav"
import { MobileNavToggle } from "@astryxdesign/core/MobileNav"
import { Button } from "@astryxdesign/core/Button"
import { HStack } from "@astryxdesign/core/HStack"
import { DewaMark } from "../dewa/DewaLogo.jsx"
import { getMode, toggleMode } from "../lib/theme.js"

const svg = (...d) => (
  <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{d}</svg>
)
const NAV = [
  { path: "/", label: "Home", icon: svg(<path key="a" d="M3 11l9-8 9 8" />, <path key="b" d="M5 10v10h14V10" />) },
  { path: "/journey", label: "Journey", icon: svg(<path key="a" d="M9 4L3 6v14l6-2 6 2 6-2V4l-6 2-6-2z" />, <path key="b" d="M9 4v14M15 6v14" />) },
  { path: "/architecture", label: "Architecture", icon: svg(<circle key="a" cx="5" cy="6" r="2" />, <circle key="b" cx="19" cy="6" r="2" />, <circle key="c" cx="12" cy="18" r="2" />, <path key="d" d="M7 7l4 9M17 7l-4 9M7 6h10" />) },
  { path: "/vibe-code", label: "Vibe Code", icon: svg(<path key="a" d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z" />) },
  { path: "/pm-log", label: "PM Log", icon: svg(<path key="a" d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z" />, <path key="b" d="M4 19a2 2 0 0 1 2-2h13" />) },
]
const Sun = () => svg(<circle key="a" cx="12" cy="12" r="4" />, <path key="b" d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M19 5l-1.5 1.5M6.5 17.5L5 19" />)
const Moon = () => svg(<path key="a" d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z" />)

export default function App() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const [navOpen, setNavOpen] = useState(false)
  const [mode, setMode] = useState(getMode())

  // { viewTransition: true } wraps the navigation in the native View Transitions
  // API → a quiet cross-fade between pages, 0 KB, reduced-motion-safe (motion.css
  // neutralises it under prefers-reduced-motion). For a shared-element MORPH,
  // name the shared node on both views — see dewa/DESIGN.md → "Motion".
  const go = (path) => (e) => { e.preventDefault(); navigate(path, { viewTransition: true }); setNavOpen(false) }

  const rail = (
    <SideNav header={<SideNavHeading icon={<DewaMark size={28} />} heading="{{PROJECT_NAME}}" subheading="DEWA · Astryx" />}>
      <SideNavSection title="App">
        {NAV.map((item) => (
          <SideNavItem key={item.path} label={item.label} icon={item.icon}
            isSelected={pathname === item.path} href={item.path} onClick={go(item.path)} />
        ))}
      </SideNavSection>
    </SideNav>
  )

  return (
    <AppShell height="fill" contentPadding={0} sideNav={rail}
      mobileNav={{ isOpen: navOpen, onOpenChange: setNavOpen, hasToggle: false, breakpoint: "lg" }}>
      <div className="content-col">
        <div className="topbar">
          <HStack gap={2} align="center">
            <MobileNavToggle label="Open menu" />
          </HStack>
          <Button variant="ghost" size="sm" isIconOnly
            label={mode === "dark" ? "Switch to light" : "Switch to dark"}
            icon={mode === "dark" ? <Sun /> : <Moon />}
            onClick={() => setMode(toggleMode())} />
        </div>
        <div className="page-scroll" key={pathname}>
          <Outlet />
        </div>
      </div>
    </AppShell>
  )
}
