// frontend/src/pages/PromotionPage.jsx
import React, { useEffect, useState } from 'react'
import { apiClient } from '../apiClient'

export default function PromotionPage() {
    const [inventoryByLocation, setInventoryByLocation] = useState({})
    const [includeService, setIncludeService] = useState(false)
    const [loading, setLoading] = useState(false)

    // Messages related to inventory loading
    const [message, setMessage] = useState('')
    const [error, setError] = useState('')

    // Messages related to the PR price update panel ONLY
    const [entryMessage, setEntryMessage] = useState('')
    const [entryMessageColor, setEntryMessageColor] = useState('red')

    const [form, setForm] = useState({
        vin_number: '',
        sale_price: '',
        discount_percent: '',
        raise_percent: '',
    })

    const role = localStorage.getItem('role')
    const userLocation = localStorage.getItem('location')

    const fetchInventory = async (opts = {}) => {
        setLoading(true)
        setError('')
        setMessage('')

        try {
            const res = await apiClient.get('/promotion/inventory', {
                params: {
                    include_service: opts.includeService ?? includeService,
                },
            })
            setInventoryByLocation(res.data || {})
        } catch (err) {
            console.error('Failed to load promotion inventory:', err)
            setError('Failed to load promotion inventory.')
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchInventory()
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    const handleToggleIncludeService = (e) => {
        const checked = e.target.checked
        setIncludeService(checked)
        fetchInventory({ includeService: checked })
    }

    const handleFormChange = (e) => {
        const { name, value } = e.target
        setForm((prev) => ({ ...prev, [name]: value }))
    }

    const resetForm = () => {
        setForm({
            vin_number: '',
            sale_price: '',
            discount_percent: '',
            raise_percent: '',
        })
    }

    const handleSubmit = async (e) => {
        e.preventDefault()

        // Clear only PR-panel messages
        setEntryMessage('')
        setEntryMessageColor('red')

        const { vin_number, sale_price, discount_percent, raise_percent } = form

        if (!vin_number.trim()) {
            setEntryMessage('VIN is required.')
            setEntryMessageColor('red')
            return
        }

        // Only one of sale_price, discount_percent, raise_percent can be used
        const filled = [sale_price, discount_percent, raise_percent].filter(
            (v) => v !== '' && v !== null
        ).length

        if (filled !== 1) {
            setEntryMessage(
                'Exactly one of Sale Price, Discount Percent, or Raise Percent must be provided.'
            )
            setEntryMessageColor('red')
            return
        }

        const payload = { vin_number }

        if (sale_price !== '') {
            payload.sale_price = Number(sale_price)
        } else if (discount_percent !== '') {
            payload.discount_percent = Number(discount_percent)
        } else if (raise_percent !== '') {
            payload.raise_percent = Number(raise_percent)
        }

        try {
            const res = await apiClient.post('/promotion/update-price', payload)

            const msg =
                res.data && res.data.detail
                    ? res.data.detail
                    : 'Price updated successfully.'

            setEntryMessage(msg)
            setEntryMessageColor('green')

            resetForm()
            await fetchInventory()
        } catch (err) {
            console.error('Failed to update price:', err)
            const backendMsg =
                err.response &&
                err.response.data &&
                err.response.data.detail
                    ? err.response.data.detail
                    : 'Failed to update price.'
            setEntryMessage(backendMsg)
            setEntryMessageColor('red')
        }
    }

    return (
        <div>
            <h2>Promotion / PR</h2>

            <p>
                Role: <strong>{role}</strong> at location{' '}
                <strong>{userLocation}</strong>
            </p>

            {loading && <p>Loading inventory...</p>}

            {/* Filter controls */}
            <div
                style={{
                    marginBottom: '1rem',
                    border: '1px solid #ccc',
                    padding: '0.75rem',
                }}
            >
                <label>
                    <input
                        type="checkbox"
                        checked={includeService}
                        onChange={handleToggleIncludeService}
                    />{' '}
                    Include cars in Service
                </label>
            </div>

            {/* Inventory tables by location */}
            <h3>Inventory by Location</h3>

            {/* Inventory-related messages appear **here**, not at the very top */}
            {message && <p style={{ color: 'green' }}>{message}</p>}
            {error && <p style={{ color: 'red' }}>{error}</p>}

            {Object.keys(inventoryByLocation).length === 0 && !loading && (
                <p>No inventory data available.</p>
            )}

            {Object.entries(inventoryByLocation).map(([location, cars]) => (
                <div
                    key={location}
                    style={{
                        marginBottom: '2rem',
                        border: '1px solid #ddd',
                        padding: '0.75rem',
                    }}
                >
                    <h4>Location: {location}</h4>
                    <table border="1" cellPadding="4" style={{ width: '100%' }}>
                        <thead>
                        <tr>
                            <th>VIN</th>
                            <th>Make</th>
                            <th>Model</th>
                            <th>Year</th>
                            <th>Mileage</th>
                            <th>Condition</th>
                            <th>Cost</th>
                            <th>Sale Price</th>
                            <th>Status</th>
                        </tr>
                        </thead>
                        <tbody>
                        {cars.map((c) => (
                            <tr key={c.vin_number}>
                                <td>{c.vin_number}</td>
                                <td>{c.make}</td>
                                <td>{c.model}</td>
                                <td>{c.year}</td>
                                <td>{c.mileage}</td>
                                <td>{c.condition_type}</td>
                                <td>{c.cost}</td>
                                <td>{c.sale_price}</td>
                                <td>{c.status}</td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                </div>
            ))}

            {/* PR entry panel */}
            <div
                style={{
                    marginTop: '2rem',
                    border: '1px solid #ccc',
                    padding: '1rem',
                }}
            >
                <h3>PR Price Update</h3>

                {/* ✅ Error/success for PR update shown RIGHT HERE */}
                {entryMessage && (
                    <p style={{ color: entryMessageColor, marginBottom: '1rem' }}>
                        {entryMessage}
                    </p>
                )}

                <p style={{ fontSize: '0.9rem' }}>
                    Enter the VIN and <strong>exactly one</strong> of:
                    <strong> Sale Price</strong>, <strong>Discount %</strong>, or{' '}
                    <strong>Raise %</strong>. PR updates are limited by:
                    <br />
                    – Max 10% up/down per update<br />
                    – Profit must stay ≥ 20%<br />
                    – Max 2 updates per car for PR (enforced on backend)
                </p>

                <form onSubmit={handleSubmit}>
                    <div>
                        <label>VIN (required)</label>
                        <br />
                        <input
                            name="vin_number"
                            value={form.vin_number}
                            onChange={handleFormChange}
                            required
                            style={{ width: '250px' }}
                        />
                    </div>

                    <div style={{ marginTop: '0.5rem' }}>
                        <label>Sale Price (optional)</label>
                        <br />
                        <input
                            type="number"
                            name="sale_price"
                            value={form.sale_price}
                            onChange={handleFormChange}
                            placeholder="Leave blank if using %"
                        />
                    </div>

                    <div style={{ marginTop: '0.5rem' }}>
                        <label>Discount Percent (optional)</label>
                        <br />
                        <input
                            type="number"
                            name="discount_percent"
                            value={form.discount_percent}
                            onChange={handleFormChange}
                            placeholder="0–10"
                        />
                    </div>

                    <div style={{ marginTop: '0.5rem' }}>
                        <label>Raise Percent (optional)</label>
                        <br />
                        <input
                            type="number"
                            name="raise_percent"
                            value={form.raise_percent}
                            onChange={handleFormChange}
                            placeholder="0–10"
                        />
                    </div>

                    <button type="submit" style={{ marginTop: '0.75rem' }}>
                        Apply Price Update
                    </button>
                    <button
                        type="button"
                        onClick={resetForm}
                        style={{ marginLeft: '0.5rem', marginTop: '0.75rem' }}
                    >
                        Clear
                    </button>
                </form>
            </div>
        </div>
    )
}
