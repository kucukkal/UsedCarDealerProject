// frontend/src/pages/SalesPage.jsx
import React, { useEffect, useState } from 'react'
import { apiClient } from '../apiClient'

export default function SalesPage() {
    const [sales, setSales] = useState([])
    const [salesLoading, setSalesLoading] = useState(false)
    const [salesError, setSalesError] = useState('')
    const [salesMessage, setSalesMessage] = useState('')

    const [search, setSearch] = useState({
        vin: '',
        make: '',
        model: '',
        condition_type: '',
        min_year: '',
        max_year: '',
        min_mileage: '',
        max_mileage: '',
        min_price: '',
        max_price: '',
    })
    const [inventoryResults, setInventoryResults] = useState([])
    const [searchError, setSearchError] = useState('')

    const [form, setForm] = useState({
        vin_number: '',
        sale_price: '',
        status: 'Under Writing',
        payment_method: 'Cash', // Cash | Credit | Loan
        deposit: '',
        interest_rate: '',
        credit_score: '',
        term_months: '',
    })
    const [formMessage, setFormMessage] = useState('')
    const [formError, setFormError] = useState('')

    const role = localStorage.getItem('role')
    const userLocation = localStorage.getItem('location')

    // -------- Load current sales --------

    const loadSales = async () => {
        setSalesLoading(true)
        setSalesError('')
        try {
            const res = await apiClient.get('/sales/')
            setSales(res.data || [])
            if (!res.data || res.data.length === 0) {
                setSalesMessage('No sales records found.')
            } else {
                setSalesMessage('')
            }
        } catch (err) {
            console.error('Failed to load sales', err)
            setSalesError('Failed to load sales.')
        } finally {
            setSalesLoading(false)
        }
    }

    useEffect(() => {
        loadSales()
    }, [])

    // -------- Inventory search for Sales --------

    const handleSearchChange = (e) => {
        const { name, value } = e.target
        setSearch((prev) => ({ ...prev, [name]: value }))
    }

    const runSearch = async (e) => {
        if (e) e.preventDefault()
        setSearchError('')
        setInventoryResults([])

        try {
            const params = {}

            if (search.vin) params.vin = search.vin
            if (search.make) params.make = search.make
            if (search.model) params.model = search.model
            if (search.condition_type) params.condition_type = search.condition_type

            if (search.min_year) params.year_min = Number(search.min_year)
            if (search.max_year) params.year_max = Number(search.max_year)
            if (search.min_mileage) params.mileage_min = Number(search.min_mileage)
            if (search.max_mileage) params.mileage_max = Number(search.max_mileage)
            if (search.min_price) params.price_min = Number(search.min_price)
            if (search.max_price) params.price_max = Number(search.max_price)

            const res = await apiClient.get('/sales/inventory-search', { params })
            setInventoryResults(res.data || [])
            if (!res.data || res.data.length === 0) {
                setSearchError('No inventory matches found for given filters.')
            }
        } catch (err) {
            console.error('Failed to search inventory for sales', err)
            setSearchError('Failed to search inventory.')
        }
    }

    const clearSearch = () => {
        setSearch({
            vin: '',
            make: '',
            model: '',
            condition_type: '',
            min_year: '',
            max_year: '',
            min_mileage: '',
            max_mileage: '',
            min_price: '',
            max_price: '',
        })
        setInventoryResults([])
        setSearchError('')
    }

    const loadCarIntoForm = (car) => {
        setForm((prev) => ({
            ...prev,
            vin_number: car.vin_number,
            sale_price: car.sale_price ?? '',
            status: 'Under Writing',
            payment_method: 'Cash',
            deposit: '',
            interest_rate: '',
            credit_score: '',
            term_months: '',
        }))
        setFormError('')
        setFormMessage('')
    }

    // -------- Sale entry / update form --------

    const handleFormChange = (e) => {
        const { name, value } = e.target

        // If payment method changes to Cash/Credit, clear loan-specific fields
        if (name === 'payment_method' && (value === 'Cash' || value === 'Credit')) {
            setForm(prev => ({
                ...prev,
                payment_method: value,
                // deposit can remain if you want, but loan fields cleared:
                interest_rate: '',
                credit_score: '',
                term_months: '',
                monthly_payment: '',
            }))
            return
        }

        setForm(prev => ({ ...prev, [name]: value }))
    }


    const resetForm = () => {
        setForm({
            vin_number: '',
            sale_price: '',
            status: 'Under Writing',
            payment_method: 'Cash',
            deposit: '',
            interest_rate: '',
            credit_score: '',
            term_months: '',
        })
        setFormError('')
        setFormMessage('')
    }

    const handleSubmitSale = async (e) => {
        e.preventDefault()
        setFormError('')
        setFormMessage('')

        if (!form.vin_number.trim()) {
            setFormError('VIN is required.')
            return
        }
        if (!form.sale_price || Number(form.sale_price) <= 0) {
            setFormError('Sale price must be greater than 0.')
            return
        }
        if (!form.status) {
            setFormError('Status is required.')
            return
        }
        if (!form.payment_method) {
            setFormError('Payment Method is required.')
            return
        }

        // For Loan, Credit Score band is required when we move to Under Contract or Under Writing
        if (
            form.payment_method === 'Loan' &&
            !form.credit_score &&
            (form.status === 'Under Contract' || form.status === 'Under Writing')
        ) {
            setFormError('Credit Score band is required for Loan.')
            return
        }

        const payload = {
            vin_number: form.vin_number,
            sale_price: Number(form.sale_price),
            status: form.status,
            payment_method: form.payment_method,
        }

        if (form.deposit !== '') payload.deposit = Number(form.deposit)
        if (form.interest_rate !== '') payload.interest_rate = Number(form.interest_rate)
        if (form.credit_score !== '') payload.credit_score = form.credit_score
        if (form.term_months !== '') payload.term_months = Number(form.term_months)

        try {
            const res = await apiClient.post('/sales/', payload)
            setFormMessage(`Sale saved. Sale ID: ${res.data.sale_id}`)
            await loadSales()
        } catch (err) {
            console.error('Failed to save sale', err)
            if (err.response && err.response.data && err.response.data.detail) {
                setFormError(err.response.data.detail)
            } else {
                setFormError('Failed to save sale.')
            }
        }
    }

    return (
        <div>
            <h2>Sales</h2>
            <p>
                Role: <strong>{role}</strong> at location <strong>{userLocation}</strong>
            </p>

            {/* -------- Current Sales Table -------- */}
            <section style={{ marginBottom: '2rem' }}>
                <h3>Current Sales</h3>
                {salesLoading && <p>Loading sales...</p>}
                {salesError && <p style={{ color: 'red' }}>{salesError}</p>}
                {salesMessage && <p>{salesMessage}</p>}

                {sales.length > 0 && (
                    <table border="1" cellPadding="4" style={{ width: '100%', marginTop: '0.5rem' }}>
                        <thead>
                        <tr>
                            <th>Sale ID</th>
                            <th>VIN</th>
                            <th>Location</th>
                            <th>Price</th>
                            <th>Status</th>
                            <th>Payment Method</th>
                            <th>Deposit</th>
                            <th>Interest Rate</th>
                            <th>Credit Score Band</th>
                            <th>Term (Months)</th>
                            <th>Monthly Payment</th>
                        </tr>
                        </thead>
                        <tbody>
                        {sales.map((s) => (
                            <tr key={s.sale_id}>
                                <td>{s.sale_id}</td>
                                <td>{s.vin_number}</td>
                                <td>{s.location}</td>
                                <td>{s.sale_price}</td>
                                <td>{s.status}</td>
                                <td>{s.payment_method}</td>
                                <td>{s.deposit}</td>
                                <td>{s.interest_rate}</td>
                                <td>{s.credit_score}</td>
                                <td>{s.term_months}</td>
                                <td>{s.monthly_payment}</td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                )}
            </section>

            {/* -------- Inventory Search Panel -------- */}
            <section style={{ marginBottom: '2rem', border: '1px solid #ccc', padding: '1rem' }}>
                <h3>Search Inventory to Add to Sales</h3>
                {searchError && <p style={{ color: 'red' }}>{searchError}</p>}

                <form onSubmit={runSearch}>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
                        <div>
                            <label>VIN</label>
                            <br />
                            <input name="vin" value={search.vin} onChange={handleSearchChange} />
                        </div>
                        <div>
                            <label>Make</label>
                            <br />
                            <input name="make" value={search.make} onChange={handleSearchChange} />
                        </div>
                        <div>
                            <label>Model</label>
                            <br />
                            <input name="model" value={search.model} onChange={handleSearchChange} />
                        </div>
                        <div>
                            <label>Condition</label>
                            <br />
                            <input
                                name="condition_type"
                                value={search.condition_type}
                                onChange={handleSearchChange}
                                placeholder="Good, Mint, Damaged..."
                            />
                        </div>
                        <div>
                            <label>Min Year</label>
                            <br />
                            <input
                                type="number"
                                name="min_year"
                                value={search.min_year}
                                onChange={handleSearchChange}
                            />
                        </div>
                        <div>
                            <label>Max Year</label>
                            <br />
                            <input
                                type="number"
                                name="max_year"
                                value={search.max_year}
                                onChange={handleSearchChange}
                            />
                        </div>
                        <div>
                            <label>Min Mileage</label>
                            <br />
                            <input
                                type="number"
                                name="min_mileage"
                                value={search.min_mileage}
                                onChange={handleSearchChange}
                            />
                        </div>
                        <div>
                            <label>Max Mileage</label>
                            <br />
                            <input
                                type="number"
                                name="max_mileage"
                                value={search.max_mileage}
                                onChange={handleSearchChange}
                            />
                        </div>
                        <div>
                            <label>Min Price</label>
                            <br />
                            <input
                                type="number"
                                name="min_price"
                                value={search.min_price}
                                onChange={handleSearchChange}
                            />
                        </div>
                        <div>
                            <label>Max Price</label>
                            <br />
                            <input
                                type="number"
                                name="max_price"
                                value={search.max_price}
                                onChange={handleSearchChange}
                            />
                        </div>
                    </div>
                    <div style={{ marginTop: '0.75rem' }}>
                        <button type="submit">Search Inventory</button>
                        <button
                            type="button"
                            onClick={clearSearch}
                            style={{ marginLeft: '0.5rem' }}
                        >
                            Clear
                        </button>
                    </div>
                </form>

                {inventoryResults.length > 0 && (
                    <div style={{ marginTop: '1rem' }}>
                        <h4>Search Results</h4>
                        <table border="1" cellPadding="4" style={{ width: '100%' }}>
                            <thead>
                            <tr>
                                <th>VIN</th>
                                <th>Make</th>
                                <th>Model</th>
                                <th>Year</th>
                                <th>Mileage</th>
                                <th>Condition</th>
                                <th>Price</th>
                                <th>Location</th>
                                <th>Status</th>
                                <th>Use</th>
                            </tr>
                            </thead>
                            <tbody>
                            {inventoryResults.map((car) => (
                                <tr key={car.vin_number}>
                                    <td>{car.vin_number}</td>
                                    <td>{car.make}</td>
                                    <td>{car.model}</td>
                                    <td>{car.year}</td>
                                    <td>{car.mileage}</td>
                                    <td>{car.condition_type}</td>
                                    <td>{car.sale_price}</td>
                                    <td>{car.location}</td>
                                    <td>{car.status}</td>
                                    <td>
                                        <button type="button" onClick={() => loadCarIntoForm(car)}>
                                            Load into Sale Form
                                        </button>
                                    </td>
                                </tr>
                            ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>

            {/* -------- Sale Entry Panel -------- */}
            <section style={{ border: '1px solid #ccc', padding: '1rem' }}>
                <h3>Create / Update Sale</h3>
                {formError && <p style={{ color: 'red' }}>{formError}</p>}
                {formMessage && <p style={{ color: 'green' }}>{formMessage}</p>}
                <p style={{ fontSize: '0.9rem' }}>
                    SalesRep can change price within <strong>±10%</strong> of the inventory sale price and
                    profit must remain at least <strong>20%</strong>. For <strong>Loan</strong> payments, a
                    Credit Score band is selected and the backend will pick a random interest rate within the
                    allowed bracket when moving to <strong>Under Contract</strong>.
                </p>

                <form onSubmit={handleSubmitSale}>
                    <div style={{ marginBottom: '0.5rem' }}>
                        <label>VIN (required)</label>
                        <br />
                        <input
                            name="vin_number"
                            value={form.vin_number}
                            onChange={handleFormChange}
                            style={{ width: '250px' }}
                            required
                        />
                    </div>

                    <div style={{ marginBottom: '0.5rem' }}>
                        <label>Sale Price (required)</label>
                        <br />
                        <input
                            type="number"
                            name="sale_price"
                            value={form.sale_price}
                            onChange={handleFormChange}
                            required
                        />
                    </div>

                    <div style={{ marginBottom: '0.5rem' }}>
                        <label>Status (required)</label>
                        <br />
                        <select name="status" value={form.status} onChange={handleFormChange}>
                            <option value="Under Writing">Under Writing</option>
                            <option value="Under Contract">Under Contract</option>
                            <option value="Sold">Sold</option>
                        </select>
                    </div>

                    <div style={{ marginBottom: '0.5rem' }}>
                        <label>Payment Method (required)</label>
                        <br />
                        <select
                            name="payment_method"
                            value={form.payment_method}
                            onChange={handleFormChange}
                        >
                            <option value="Cash">Cash</option>
                            <option value="Credit">Credit</option>
                            <option value="Loan">Loan</option>
                        </select>
                    </div>

                    {/* Loan-related fields */}
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', marginTop: '0.5rem' }}>
                        <div>
                            <label>Deposit</label>
                            <br />
                            <input
                                type="number"
                                name="deposit"
                                value={form.deposit}
                                onChange={handleFormChange}
                            />
                        </div>
                        <div>
                            <label>Interest Rate (%)</label>
                            <br />
                            <input
                                type="number"
                                name="interest_rate"
                                value={form.interest_rate}
                                onChange={handleFormChange}
                                step="0.01"
                                placeholder="Leave empty to auto-pick for Loan"
                            />
                        </div>
                        <div>
                            <label>Credit Score Band</label>
                            <br />
                            <select
                                name="credit_score"
                                value={form.credit_score}
                                onChange={handleFormChange}
                            >
                                <option value="">-- Select --</option>
                                <option value="Excellent">Excellent (0–0.9%)</option>
                                <option value="Very Good">Very Good (1–2%)</option>
                                <option value="Good">Good (2–5%)</option>
                                <option value="Average">Average (5–7%)</option>
                                <option value="Poor">Poor (7–10%)</option>
                            </select>
                        </div>
                        <div>
                            <label>Term (Months)</label>
                            <br />
                            <input
                                type="number"
                                name="term_months"
                                value={form.term_months}
                                onChange={handleFormChange}
                            />
                        </div>
                    </div>

                    <div style={{ marginTop: '0.75rem' }}>
                        <button type="submit">Save Sale</button>
                        <button
                            type="button"
                            onClick={resetForm}
                            style={{ marginLeft: '0.5rem' }}
                        >
                            Clear
                        </button>
                    </div>
                </form>
            </section>
        </div>
    )
}
