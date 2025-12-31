"use client";

import Sidebar from "./Sidebar";

interface MainLayoutProps {
    children: React.ReactNode;
    title?: React.ReactNode;
    actions?: React.ReactNode;
} 

export default function MainLayout({ children, title, actions }: MainLayoutProps) {
    return (
        <div className="main-layout">
            <Sidebar />
            <main className="main-content">
                {/* Header */}
                {(title || actions) && (
                    <header className="header">
                        <h1 className="header-title">{title}</h1>
                        <div className="header-actions">{actions}</div>
                    </header>
                )}
                {/* Page Content */}
                <div style={{ padding: "2rem" }}>
                    {children}
                </div>
            </main>
        </div>
    );
}
