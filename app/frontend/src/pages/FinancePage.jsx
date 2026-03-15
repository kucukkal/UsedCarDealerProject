// frontend/src/pages/FinancePage.jsx
import React, { useEffect, useState } from 'react'
import { apiClient } from '../apiClient'

export default function FinancePage() {
    const [rows, setRows] = useState([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [message, setMessage] = useState('')

    const [snapshotLoading, setSnapshotLoading] = useState(false)
    const [snapshotMessage, setSnapshotMessage] = useState('')
    const [snapshotError, setSnapshotError] = useState('')

    const [summary, setSummary] = useState(null)
    const [summaryLoading, setSummaryLoading] = useState(false)
    const [summaryError, setSummaryError] = useState('')

    // NEW: Customers table state
    const [customers, setCustomers] = useState([])
    const [customersLoading, setCustomersLoading] = useState(false)
    const [customersError, setCustomersError] = useState('')

    const role = localStorage.getItem('role')
    const userLocation = localStorage.getItem('location')

    // -------- Load finance table --------
    const loadFinance = async () => {
        setLoading(true)
        setError('')
        setMessage('')
        try {
            const res = await apiClient.get('/finance/')
            const data = res.data || []
            setRows(data)
            if (!data.length) {
                setMessage('No finance records found. Run the snapshot to populate data.')
            }
        } catch (err) {
            console.error('Failed to load finance data', err)
            setError('Failed to load finance data.')
        } finally {
            setLoading(false)
        }
    }

    // -------- Load customers table --------
    const loadCustomers = async () => {
        setCustomersLoading(true)
        setCustomersError('')
        try {
            const res = await apiClient.get('/finance/customers')
            setCustomers(res.data || [])
        } catch (err) {
            console.error('Failed to load customers', err)
            setCustomersError('Failed to load customers table.')
        } finally {
            setCustomersLoading(false)
        }
    }

    useEffect(() => {
        loadFinance()
        loadCustomers()
    }, [])

    // -------- Trigger snapshot from UI --------
    const runSnapshot = async () => {
        setSnapshotLoading(true)
        setSnapshotError('')
        setSnapshotMessage('')
        try {
            const res = await apiClient.post('/finance/run-daily-snapshot')
            setSnapshotMessage((res.data && res.data.detail) || 'Finance snapshot rebuilt successfully.')

            // Reload tables after snapshot
            await loadFinance()
            await loadCustomers()
        } catch (err) {
            console.error('Failed to run finance snapshot', err)
            if (err.response && err.response.data && err.response.data.detail) {
                setSnapshotError(err.response.data.detail)
            } else {
                setSnapshotError('Failed to run finance snapshot.')
            }
        } finally {
            setSnapshotLoading(false)
        }
    }

    // -------- Load summary metrics --------
    const loadSummary = async () => {
        setSummaryLoading(true)
        setSummaryError('')
        setSummary(null)
        try {
            const res = await apiClient.get('/finance/summary')
            setSummary(res.data || null)
        } catch (err) {
            console.error('Failed to load finance summary', err)
            setSummaryError('Failed to load finance summary.')
        } finally {
            setSummaryLoading(false)
        }
    }

    return (
        <div>
            <h2>Finance</h2>
            <p>
                Role: <strong>{role}</strong> at location <strong>{userLocation}</strong>
            </p>

            {/* Controls */}
            <section style={{ marginBottom: '1.5rem' }}>
                <button onClick={runSnapshot} disabled={snapshotLoading}>
                    {snapshotLoading ? 'Running Snapshot...' : 'Run Finance Snapshot Now'}
                </button>

                {snapshotMessage && (
                    <p style={{ color: 'green', marginTop: '0.5rem' }}>{snapshotMessage}</p>
                )}
                {snapshotError && <p style={{ color: 'red', marginTop: '0.5rem' }}>{snapshotError}</p>}

                <div style={{ marginTop: '1rem' }}>
                    <button onClick={loadSummary} disabled={summaryLoading}>
                        {summaryLoading ? 'Loading Summary...' : 'Show Finance Summary'}
                    </button>
                    {summaryError && <p style={{ color: 'red', marginTop: '0.5rem' }}>{summaryError}</p>}
                </div>
            </section>

            {/* Finance Summary Table */}
            {summary && (
                <section style={{ marginBottom: '2rem', border: '1px solid #ccc', padding: '1rem' }}>
                    <h3>Finance Summary</h3>
                    <table border="1" cellPadding="4" style={{ width: '100%', marginTop: '0.5rem' }}>
                        <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Amount (USD)</th>
                        </tr>
                        </thead>
                        <tbody>
                        <tr>
                            <td>Total Amount of Assets (Inventory cost, status ≠ Sold)</td>
                            <td>{Number(summary.total_assets || 0).toFixed(2)}</td>
                        </tr>
                        <tr>
                            <td>Projected Sale Amount (Inventory sale_price, status ≠ Sold)</td>
                            <td>{Number(summary.projected_sale || 0).toFixed(2)}</td>
                        </tr>
                        <tr>
                            <td>Projected Profit Amount</td>
                            <td>{Number(summary.projected_profit || 0).toFixed(2)}</td>
                        </tr>
                        <tr>
                            <td>Total Available Funds Projected (Final sale price of all Sold cars)</td>
                            <td>{Number(summary.total_final_sold || 0).toFixed(2)}</td>
                        </tr>
                        <tr>
                            <td>Total Tax Amount (Sold cars)</td>
                            <td>{Number(summary.total_tax_sold || 0).toFixed(2)}</td>
                        </tr>
                        <tr>
                            <td>Total Available Funds (Cash/Credit final sale + Loan amount paid)</td>
                            <td>{Number(summary.total_available_funds || 0).toFixed(2)}</td>
                        </tr>
                        <tr>
                            <td>Total Profit Now</td>
                            <td>{Number(summary.total_profit_now || 0).toFixed(2)}</td>
                        </tr>
                        </tbody>
                    </table>
                </section>
            )}

            {/* Finance Table */}
            <section>
                <h3>Finance Snapshot</h3>
                {loading && <p>Loading finance data...</p>}
                {error && <p style={{ color: 'red' }}>{error}</p>}
                {message && <p>{message}</p>}

                {rows.length > 0 && (
                    <table border="1" cellPadding="4" style={{ width: '100%', marginTop: '0.5rem' }}>
                        <thead>
                        <tr>
                            <th>ID</th>
                            <th>Finance ID</th>
                            <th>Sale ID</th>
                            <th>VIN</th>
                            <th>Status</th>
                            <th>Payment Type</th>
                            <th>Cost</th>
                            <th>Sale Price</th>
                            <th>Deposit</th>
                            <th>Loan Term</th>
                            <th>Loan Interest</th>
                            <th>Monthly Payment</th>
                            <th>CC Fee</th>
                            <th>Tax</th>
                            <th>Final Sale Price</th>
                            <th>Amount Paid</th>
                            <th>Amount Remaining</th>
                            <th>Net Profit</th>
                            <th>Profit Now</th>
                            <th>Sale Date</th>
                        </tr>
                        </thead>
                        <tbody>
                        {rows.map((r) => (
                            <tr key={r.id}>
                                <td>{r.id}</td>
                                <td>{r.finance_id}</td>
                                <td>{r.sale_id}</td>
                                <td>{r.vin_number}</td>
                                <td>{r.status}</td>
                                <td>{r.payment_type || ''}</td>
                                <td>{r.cost}</td>
                                <td>{r.sale_price}</td>
                                <td>{r.deposit}</td>
                                <td>{r.loan_term ?? ''}</td>
                                <td>{r.loan_interest ?? ''}</td>
                                <td>{r.monthly_payment ?? ''}</td>
                                <td>{r.cc_fee}</td>
                                <td>{r.tax}</td>
                                <td>{r.final_sale_price}</td>
                                <td>{r.amount_paid}</td>
                                <td>{r.amount_remaining}</td>
                                <td>{r.net_profit}</td>
                                <td>{r.profit_now}</td>
                                <td>{r.sale_date || ''}</td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                )}
            </section>

            {/* Customers Table */}
            <section style={{ marginTop: '2rem' }}>
                <h3>Customers</h3>

                {customersLoading && <p>Loading customers...</p>}
                {customersError && <p style={{ color: 'red' }}>{customersError}</p>}

                {!customersLoading && !customersError && customers.length === 0 && (
                    <p>No customer records found.</p>
                )}

                {customers.length > 0 && (
                    <table border="1" cellPadding="4" style={{ width: '100%', marginTop: '0.5rem' }}>
                        <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Zip</th>
                            <th>City</th>
                            <th>State</th>
                            <th>Phone</th>

                            <th>VIN</th>
                            <th>Make</th>
                            <th>Model</th>
                            <th>SubModel</th>
                            <th>Type</th>
                            <th>Color</th>
                            <th>Antique</th>
                            <th>Condition</th>

                            <th>Year</th>
                            <th>Mileage</th>
                            <th>Sale Price</th>
                            <th>Location</th>
                            <th>Created At</th>
                        </tr>
                        </thead>
                        <tbody>
                        {customers.map((c) => (
                            <tr key={c.id}>
                                <td>{c.id}</td>
                                <td>{c.customer_name}</td>
                                <td>{c.customer_zipcode}</td>
                                <td>{c.customer_city}</td>
                                <td>{c.customer_state}</td>
                                <td>{c.customer_phone}</td>

                                <td>{c.vin_number}</td>
                                <td>{c.make}</td>
                                <td>{c.model}</td>
                                <td>{c.sub_model || ''}</td>
                                <td>{c.vehicle_type || ''}</td>
                                <td>{c.color || ''}</td>
                                <td>{String(c.antique ?? '')}</td>
                                <td>{c.condition_type || ''}</td>

                                <td>{c.year}</td>
                                <td>{c.mileage}</td>
                                <td>{c.sale_price}</td>
                                <td>{c.location}</td>
                                <td>{c.created_at || ''}</td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                )}
            </section>
        </div>
    )
}
