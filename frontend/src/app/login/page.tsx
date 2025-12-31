"use client";

import { useState } from "react";
import Link from "next/link";
import { MailIcon, LockIcon, EyeIcon, EyeOffIcon } from "@/components/icons/Icons";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        // Simulate login - in real app, this would call auth API
        setTimeout(() => {
            window.location.href = "/";
        }, 1000);
    };

    return (
        <div
            style={{
                minHeight: "100vh",
                background: "var(--bg-primary)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                padding: "2rem",
            }}
        >
            <div
                style={{
                    background: "var(--bg-card)",
                    border: "1px solid var(--border-color)",
                    borderRadius: "16px",
                    padding: "2.5rem",
                    width: "100%",
                    maxWidth: "420px",
                }}
            >
                {/* Logo */}
                <div style={{ textAlign: "center", marginBottom: "2rem" }}>
                    <div
                        style={{
                            width: "64px",
                            height: "64px",
                            background: "var(--gradient-emerald)",
                            borderRadius: "16px",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            margin: "0 auto 1rem",
                        }}
                    >
                        <span style={{ fontSize: "1.5rem", color: "white", fontWeight: 700 }}>CIP</span>
                    </div>
                    <h1 style={{ fontSize: "1.75rem", marginBottom: "0.5rem" }}>Welcome back</h1>
                    <p style={{ color: "var(--text-muted)" }}>Sign in to your account to continue</p>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit}>
                    {/* Email */}
                    <div className="form-group">
                        <label className="form-label">Email</label>
                        <div style={{ position: "relative" }}>
                            <span
                                style={{
                                    position: "absolute",
                                    left: "1rem",
                                    top: "50%",
                                    transform: "translateY(-50%)",
                                    color: "var(--text-muted)",
                                    display: "inline-flex",
                                    alignItems: "center",
                                }}
                            >
                                <MailIcon />
                            </span>
                            <input
                                type="email"
                                className="input"
                                style={{ paddingLeft: "2.75rem" }}
                                placeholder="you@example.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    {/* Password */}
                    <div className="form-group">
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                            <label className="form-label" style={{ margin: 0 }}>Password</label>
                            <a href="#" style={{ fontSize: "0.875rem", color: "var(--emerald-400)" }}>
                                Forgot password?
                            </a>
                        </div>
                        <div style={{ position: "relative" }}>
                            <span
                                style={{
                                    position: "absolute",
                                    left: "1rem",
                                    top: "50%",
                                    transform: "translateY(-50%)",
                                    color: "var(--text-muted)",
                                    display: "inline-flex",
                                    alignItems: "center",
                                }}
                            >
                                <LockIcon />
                            </span>
                            <input
                                type={showPassword ? "text" : "password"}
                                className="input"
                                style={{ paddingLeft: "2.75rem", paddingRight: "2.75rem" }}
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                style={{
                                    position: "absolute",
                                    right: "1rem",
                                    top: "50%",
                                    transform: "translateY(-50%)",
                                    background: "none",
                                    border: "none",
                                    color: "var(--text-muted)",
                                    cursor: "pointer",
                                    display: "inline-flex",
                                    alignItems: "center",
                                }}
                            >
                                {showPassword ? <EyeOffIcon /> : <EyeIcon />}
                            </button>
                        </div>
                    </div>

                    {/* Sign In Button */}
                    <button
                        type="submit"
                        className="btn btn-primary"
                        style={{ width: "100%", marginTop: "1rem", padding: "1rem" }}
                        disabled={loading}
                    >
                        {loading ? "Signing in..." : "Sign in"}
                    </button>
                </form>

                {/* Divider */}
                <div
                    style={{
                        display: "flex",
                        alignItems: "center",
                        margin: "1.5rem 0",
                        gap: "1rem",
                    }}
                >
                    <div style={{ flex: 1, height: "1px", background: "var(--border-color)" }}></div>
                    <span style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>OR CONTINUE WITH</span>
                    <div style={{ flex: 1, height: "1px", background: "var(--border-color)" }}></div>
                </div>

                {/* Google Button */}
                <button
                    type="button"
                    className="btn btn-secondary"
                    style={{ width: "100%", padding: "0.875rem" }}
                >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                    </svg>
                    Continue with Google
                </button>

                {/* Sign Up Link */}
                <p style={{ textAlign: "center", marginTop: "1.5rem", color: "var(--text-muted)" }}>
                    Don't have an account?{" "}
                    <Link href="/register" style={{ color: "var(--emerald-400)" }}>
                        Sign up
                    </Link>
                </p>
            </div>
        </div>
    );
}
