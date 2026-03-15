import React from 'react'
import { Routes, Route, Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import HomePage from './pages/HomePage'
import InventoryPage from './pages/InventoryPage'
import SalesPage from './pages/SalesPage'
import ServicePage from './pages/ServicePage'
import FinancePage from './pages/FinancePage'
import PromotionPage from './pages/PromotionPage'
import AdminPage from './pages/AdminPage'

// inside your <Routes>:


function RequireAuth({ children }) {
    const token = localStorage.getItem('token')
    const location = useLocation()

    if (!token) {
        // Not logged in → send to login, remember where they tried to go
        return <Navigate to="/login" state={{ from: location }} replace />
    }

    return children
}

export default function App() {
    const navigate = useNavigate()

    const handleLogout = () => {
        localStorage.removeItem('token')
        localStorage.removeItem('role')
        localStorage.removeItem('username')
        localStorage.removeItem('location')

        navigate('/login', { replace: true })
    }

    const token = localStorage.getItem('token')

    return (
        <div>
            <nav
                style={{
                    padding: '1rem',
                    borderBottom: '1px solid #ccc',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                }}
            >
                {/* LEFT SIDE: NAV LINKS */}
                <div>
                    {(() => {
                        const role = localStorage.getItem('role')

                        return (
                            <>
                                {/* Always show Home + Login */}
                                <Link to="/home">Home</Link> |{' '}
                                <Link to="/login">Login</Link>

                                {/* Admin */}
                                {role === 'Admin' && (
                                    <>
                                        {' | '}<Link to="/inventory">Inventory</Link>
                                        {' | '}<Link to="/sales">Sales</Link>
                                        {' | '}<Link to="/service">Service</Link>
                                        {' | '}<Link to="/finance">Finance</Link>
                                        {' | '}<Link to="/promotion">Promotion</Link>
                                        {' | '}<Link to="/admin">Admin – User Management</Link>
                                    </>
                                )}

                                {/* PR: Inventory + Promotion only */}
                                {role === 'PR' && (
                                    <>
                                        {' | '}<Link to="/promotion">Promotion</Link>
                                    </>
                                )}

                                {/* Finance: Sales + Finance only */}
                                {role === 'Finance' && (
                                    <>
                                        {' | '}<Link to="/finance">Finance</Link>
                                    </>
                                )}

                                {/* BuyerRep: Inventory only */}
                                {role === 'BuyerRep' && (
                                    <>
                                        {' | '}<Link to="/inventory">Inventory</Link>
                                    </>
                                )}

                                {/* SalesRep: Inventory + Sales + Promotion */}
                                {role === 'SalesRep' && (
                                    <>
                                        {' | '}<Link to="/sales">Sales</Link>
                                    </>
                                )}

                                {/* ServiceRep: Service only */}
                                {role === 'ServiceRep' && (
                                    <>
                                        {' | '}<Link to="/service">Service</Link>
                                    </>
                                )}
                            </>
                        )
                    })()}
                </div>

                {/* RIGHT SIDE: WELCOME + LOGOUT */}
                <div>
                    {token && (
                        <>
              <span style={{ marginRight: '15px', fontWeight: 'bold' }}>
                Welcome, {localStorage.getItem('username')}
              </span>
                            <button
                                onClick={handleLogout}
                                style={{
                                    cursor: 'pointer',
                                    background: 'none',
                                    border: '1px solid #666',
                                    padding: '4px 8px',
                                    borderRadius: '4px',
                                }}
                            >
                                Logout
                            </button>
                        </>
                    )}
                </div>
            </nav>

            {/* MAIN CONTENT / ROUTES */}
            <div style={{ padding: '1rem' }}>
                <Routes>
                    {/* Default: always hit login first */}
                    <Route path="/" element={<Navigate to="/login" replace />} />

                    <Route path="/login" element={<LoginPage />} />

                    {/* Everything below this is protected */}
                    <Route
                        path="/home"
                        element={
                            <RequireAuth>
                                <HomePage />
                            </RequireAuth>
                        }
                    />
                    <Route
                        path="/inventory"
                        element={
                            <RequireAuth>
                                <InventoryPage />
                            </RequireAuth>
                        }
                    />
                    <Route
                        path="/sales"
                        element={
                            <RequireAuth>
                                <SalesPage />
                            </RequireAuth>
                        }
                    />
                    <Route
                        path="/service"
                        element={
                            <RequireAuth>
                                <ServicePage />
                            </RequireAuth>
                        }
                    />
                    <Route
                        path="/finance"
                        element={
                            <RequireAuth>
                                <FinancePage />
                            </RequireAuth>
                        }
                    />
                    <Route
                        path="/admin"
                        element={
                            <RequireAuth>
                                <AdminPage />
                            </RequireAuth>
                        }
                    />
                    <Route
                        path="/promotion"
                        element={
                            <RequireAuth>
                                <PromotionPage />
                            </RequireAuth>
                        }
                    />

                    {/* Any unknown route → go to login */}
                    <Route path="*" element={<Navigate to="/login" replace />} />
                </Routes>
            </div>
        </div>
    )
}
