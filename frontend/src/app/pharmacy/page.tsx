"use client";

import { useEffect, useState } from "react";
import MainLayout from "@/components/layout/MainLayout";
import { api, Medicine } from "@/lib/api";
import { PharmacyIcon, PlusIcon, WarningIcon, SearchIcon, PackageIcon, NoteIcon, ClipboardIcon, TrashIcon, SaveIcon } from "@/components/icons/Icons";

export default function PharmacyPage() {
    const [medicines, setMedicines] = useState<Medicine[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [sortBy, setSortBy] = useState("name-asc");
    const [filterBy, setFilterBy] = useState("all");
    const [showModal, setShowModal] = useState(false);
    const [editingMedicine, setEditingMedicine] = useState<Medicine | null>(null);

    // Form state
    const [formData, setFormData] = useState({
        name: "",
        description: "",
        stock_level: 0,
    });

    useEffect(() => {
        loadMedicines();
    }, []);

    const loadMedicines = async () => {
        try {
            setLoading(true);
            const data = await api.getMedicines();
            setMedicines(data);
        } catch (err) {
            setError("Failed to load medicines");
        } finally {
            setLoading(false);
        }
    };

    // Filter and sort medicines
    const getFilteredMedicines = () => {
        let filtered = [...medicines];

        // Search filter
        if (searchQuery) {
            filtered = filtered.filter(
                (m) =>
                    m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    m.description.toLowerCase().includes(searchQuery.toLowerCase())
            );
        }

        // Stock filter
        if (filterBy === "low-stock") {
            filtered = filtered.filter((m) => m.stock_level > 0 && m.stock_level < 10);
        } else if (filterBy === "out-of-stock") {
            filtered = filtered.filter((m) => m.stock_level === 0);
        } else if (filterBy === "in-stock") {
            filtered = filtered.filter((m) => m.stock_level > 0);
        }

        // Sorting
        filtered.sort((a, b) => {
            switch (sortBy) {
                case "name-asc":
                    return a.name.localeCompare(b.name);
                case "name-desc":
                    return b.name.localeCompare(a.name);
                case "stock-low":
                    return a.stock_level - b.stock_level;
                case "stock-high":
                    return b.stock_level - a.stock_level;
                default:
                    return 0;
            }
        });

        return filtered;
    };

    const filteredMedicines = getFilteredMedicines();

    // Stats
    const totalMedicines = medicines.length;
    const lowStock = medicines.filter((m) => m.stock_level > 0 && m.stock_level < 10).length;
    const outOfStock = medicines.filter((m) => m.stock_level === 0).length;

    const openAddModal = () => {
        setEditingMedicine(null);
        setFormData({ name: "", description: "", stock_level: 0 });
        setShowModal(true);
    };

    const openEditModal = (med: Medicine) => {
        setEditingMedicine(med);
        setFormData({ name: med.name, description: med.description, stock_level: med.stock_level });
        setShowModal(true);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            if (editingMedicine) {
                await api.updateMedicine(editingMedicine.id, formData);
            } else {
                await api.addMedicine(formData);
            }
            setShowModal(false);
            loadMedicines();
        } catch (err) {
            alert("Failed to save medicine");
        }
    };

    const handleDelete = async (id: number, name: string) => {
        if (!confirm(`Are you sure you want to delete "${name}"?`)) return;
        try {
            await api.deleteMedicine(id);
            loadMedicines();
        } catch (err) {
            alert("Failed to delete medicine");
        }
    };

    const getStockBadge = (stock: number) => {
        if (stock === 0) return <span className="badge badge-error">Out of Stock</span>;
        if (stock < 10) return <span className="badge badge-warning">{stock} units</span>;
        if (stock < 50) return <span className="badge badge-info">{stock} units</span>;
        return <span className="badge badge-success">{stock} units</span>;
    };

    return (
        <MainLayout
            title={<><PharmacyIcon className="inline mr-2"/> Pharmacy Management</>}
            actions={
                <button onClick={openAddModal} className="btn btn-primary">
                    <PlusIcon className="inline mr-2"/> Add Medicine
                </button>
            }
        >
            {/* Stats Cards */}
            <div className="stats-grid" style={{ marginBottom: "2rem" }}>
                <div className="stat-card">
                    <div className="stat-icon emerald"><PharmacyIcon /></div>
                    <div>
                        <div className="stat-value">{totalMedicines}</div>
                        <div className="stat-label">Total Medicines</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon" style={{ background: "rgba(234, 179, 8, 0.2)", color: "#facc15" }}><WarningIcon /></div>
                    <div>
                        <div className="stat-value">{lowStock}</div>
                        <div className="stat-label">Low Stock (&lt;10)</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon" style={{ background: "rgba(239, 68, 68, 0.2)", color: "#f87171" }}><PackageIcon /></div>
                    <div>
                        <div className="stat-value">{outOfStock}</div>
                        <div className="stat-label">Out of Stock</div>
                    </div>
                </div>
            </div>

            {/* Search and Filter Bar */}
            <div
                style={{
                    display: "flex",
                    gap: "1rem",
                    marginBottom: "1.5rem",
                    flexWrap: "wrap",
                }}
            >
                <input
                    type="text"
                    className="input"
                    style={{ flex: 1, minWidth: "250px" }}
                    placeholder="Search medicines..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
                <select className="input" style={{ width: "180px" }} value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
                    <option value="name-asc">Name (A-Z)</option>
                    <option value="name-desc">Name (Z-A)</option>
                    <option value="stock-low">Stock (Low→High)</option>
                    <option value="stock-high">Stock (High→Low)</option>
                </select>
                <select className="input" style={{ width: "180px" }} value={filterBy} onChange={(e) => setFilterBy(e.target.value)}>
                    <option value="all">All Medicines</option>
                    <option value="low-stock">Low Stock (&lt;10)</option>
                    <option value="out-of-stock">Out of Stock</option>
                    <option value="in-stock">In Stock</option>
                </select>
            </div>

            {/* Loading */}
            {loading && (
                <div className="empty-state">
                    <div className="spinner" style={{ margin: "0 auto" }}></div>
                </div>
            )}

            {/* Error */}
            {error && (
                <div className="card" style={{ borderColor: "var(--error)" }}>
                    <p style={{ color: "var(--error)", display: "flex", gap: "0.5rem", alignItems: "center" }}><WarningIcon />{error}</p>
                </div>
            )}

            {/* Medicine Table */}
            {!loading && !error && (
                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Name</th>
                                <th>Description</th>
                                <th>Stock Level</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredMedicines.length > 0 ? (
                                filteredMedicines.map((med) => (
                                    <tr key={med.id}>
                                        <td>{med.id}</td>
                                        <td><strong>{med.name}</strong></td>
                                        <td style={{ color: "var(--text-secondary)" }}>{med.description}</td>
                                        <td>{getStockBadge(med.stock_level)}</td>
                                        <td>
                                            <div style={{ display: "flex", gap: "0.5rem" }}>
                                                <button
                                                    onClick={() => openEditModal(med)}
                                                    className="btn btn-outline"
                                                    style={{ padding: "0.25rem 0.75rem", fontSize: "0.75rem" }}
                                                >
                                                    <NoteIcon className="inline mr-2" /> Edit
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(med.id, med.name)}
                                                    className="btn btn-danger"
                                                    style={{ padding: "0.25rem 0.75rem", fontSize: "0.75rem" }}
                                                >
                                                    <TrashIcon />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan={5}>
                                        <div className="empty-state">
                                            <div className="empty-state-icon"><ClipboardIcon /></div>
                                            <div className="empty-state-title">No medicines found</div>
                                            <div className="empty-state-text">
                                                {searchQuery || filterBy !== "all"
                                                    ? "Try adjusting your search or filters"
                                                    : "Click 'Add Medicine' to get started"}
                                            </div>
                                        </div>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Modal */}
            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">{editingMedicine ? "Edit Medicine" : "Add Medicine"}</h3>
                            <button className="modal-close" onClick={() => setShowModal(false)}>
                                ×
                            </button>
                        </div>
                        <form onSubmit={handleSubmit}>
                            <div className="form-group">
                                <label className="form-label">
                                    Medicine Name<span className="required">*</span>
                                </label>
                                <input
                                    type="text"
                                    className="input"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    required
                                    placeholder="e.g., Paracetamol"
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Description</label>
                                <textarea
                                    className="input"
                                    style={{ minHeight: "80px" }}
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                    placeholder="e.g., Pain reliever and fever reducer"
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">
                                    Stock Level<span className="required">*</span>
                                </label>
                                <input
                                    type="number"
                                    className="input"
                                    min="0"
                                    value={formData.stock_level}
                                    onChange={(e) => setFormData({ ...formData, stock_level: parseInt(e.target.value) || 0 })}
                                    required
                                />
                            </div>
                            <div style={{ display: "flex", gap: "1rem", marginTop: "1.5rem" }}>
                                <button type="button" className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setShowModal(false)}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                                    <SaveIcon className="inline mr-2" /> Save
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </MainLayout>
    );
}
