"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { HomeIcon, PlusIcon, PharmacyIcon, RobotIcon } from "@/components/icons/Icons";

const navItems = [
    { href: "/", label: "Dashboard", icon: <HomeIcon className="nav-svg" /> },
    { href: "/patient/new", label: "Add Patient", icon: <PlusIcon className="nav-svg" /> },
    { href: "/pharmacy", label: "Pharmacy", icon: <PharmacyIcon className="nav-svg" /> },
    { href: "/fl-dashboard", label: "AI Learning", icon: <RobotIcon className="nav-svg" /> },
];

export default function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className="sidebar">
            {/* Logo */}
            <div className="logo">
                <div className="logo-icon">CIP</div>
                <div className="logo-text">
                    Clinical<span>Intelligence</span>
                </div>
            </div>

            {/* Navigation */}
            <nav className="nav-section" style={{ flex: 1 }}>
                {navItems.map((item) => (
                    <Link
                        key={item.href}
                        href={item.href}
                        className={`nav-item ${pathname === item.href ? "active" : ""}`}
                    >
                        <span className="nav-icon">{item.icon}</span>
                        <span>{item.label}</span>
                    </Link>
                ))}
            </nav>

            {/* Footer */}
            <div style={{ padding: "1rem", borderTop: "1px solid var(--border-color)" }}>
                <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", textAlign: "center" }}>
                    © 2025 Clinical Intelligence Platform
                </p>
            </div>
        </aside>
    );
}
