// frontend/src/pages/ServicePage.jsx
import React, { useEffect, useState } from 'react'
import { apiClient } from '../apiClient'

export default function ServicePage() {
    const [records, setRecords] = useState([])
    const [message, setMessage] = useState('')
    const [editError, setEditError] = useState('')

    // Simple entry form state
    const [simpleForm, setSimpleForm] = useState({
        vin_number: '',
        seriousness_level: '',
        estimated_days: '',
        cost_added: '',
    })
    const [simpleError, setSimpleError] = useState('')

    const [editingServiceId, setEditingServiceId] = useState(null)
    const [editForm, setEditForm] = useState({
        seriousness_level: '',
        estimated_days: '',
        service_start_date: '',
        cost_added: '',
    })

    const fetchService = async () => {
        try {
            const res = await apiClient.get('/service/')
            setRecords(res.data)
            setMessage('')
        } catch (err) {
            console.error('Failed to load service records:', err)
            setMessage('Failed to load service records')
        }
    }

    useEffect(() => {
        fetchService()
    }, [])

    const formatDate = (isoDateOrNull) => {
        if (!isoDateOrNull) return ''
        const d = new Date(isoDateOrNull)
        const mm = String(d.getMonth() + 1).padStart(2, '0')
        const dd = String(d.getDate()).padStart(2, '0')
        const yyyy = d.getFullYear()
        return `${mm}/${dd}/${yyyy}`
    }

    // ------ SIMPLE ENTRY HANDLERS ------

    const handleSimpleChange = (e) => {
        const { name, value } = e.target
        setSimpleForm((prev) => ({ ...prev, [name]: value }))
    }

    const handleSimpleSubmit = async (e) => {
        e.preventDefault()
        setSimpleError('')
        setMessage('')

        if (!simpleForm.vin_number || !simpleForm.seriousness_level) {
            setSimpleError('VIN and Seriousness are required.')
            return
        }

        try {
            const payload = {
                vin_number: simpleForm.vin_number,
                seriousness_level: simpleForm.seriousness_level,
                estimated_days: simpleForm.estimated_days
                    ? Number(simpleForm.estimated_days)
                    : undefined,
                cost_added: simpleForm.cost_added
                    ? Number(simpleForm.cost_added)
                    : undefined,
            }

            const res = await apiClient.post('/service/simple-entry', payload)
            console.log('Simple service entry response:', res.data)

            setMessage('Service record created')
            setSimpleForm({
                vin_number: '',
                seriousness_level: '',
                estimated_days: '',
                cost_added: '',
            })
            await fetchService()
        } catch (err) {
            console.error('Failed to create service record:', err)
            if (err.response?.data?.detail) {
                setSimpleError(err.response.data.detail)
            } else {
                setSimpleError('Failed to create service record')
            }
        }
    }

    // ------ EDIT HANDLERS ------

    const startEdit = (rec) => {
        setEditingServiceId(rec.service_id)
        setEditError('')
        setEditForm({
            seriousness_level: rec.seriousness_level,
            estimated_days: String(rec.estimated_days),
            service_start_date: formatDate(rec.service_start_date || rec.created_at),
            cost_added: rec.cost_added != null ? String(rec.cost_added) : '',
        })
    }

    const cancelEdit = () => {
        setEditingServiceId(null)
        setEditForm({
            seriousness_level: '',
            estimated_days: '',
            service_start_date: '',
            cost_added: '',
        })
        setEditError('')
    }

    const handleEditChange = (e) => {
        const { name, value } = e.target
        setEditForm((prev) => ({ ...prev, [name]: value }))
    }

    const parseMMDDYYYYToISO = (value) => {
        const parts = value.split('/')
        if (parts.length !== 3) return null
        const [mm, dd, yyyy] = parts
        if (!mm || !dd || !yyyy) return null
        return `${yyyy}-${mm.padStart(2, '0')}-${dd.padStart(2, '0')}`
    }

    const handleUpdateService = async (e) => {
        e.preventDefault()
        if (!editingServiceId) return

        setEditError('')
        setMessage('')

        const isoDate = parseMMDDYYYYToISO(editForm.service_start_date)
        if (!isoDate) {
            setEditError('Service Start Date must be in MM/DD/YYYY format.')
            return
        }

        try {
            const payload = {
                seriousness_level: editForm.seriousness_level,
                estimated_days: Number(editForm.estimated_days),
                service_start_date: isoDate,
                cost_added:
                    editForm.cost_added !== '' ? Number(editForm.cost_added) : undefined,
            }

            const res = await apiClient.patch(`/service/${editingServiceId}`, payload)
            console.log('Update service response:', res.data)

            setMessage('Service record updated')
            setEditingServiceId(null)
            await fetchService()
        } catch (err) {
            console.error('Failed to update service record:', err)
            if (err.response?.data?.detail) {
                setEditError(err.response.data.detail)
            } else {
                setEditError('Failed to update service record')
            }
        }

    }

const handleCompleteService = async () => {
    if (!editingServiceId) return

    setEditError('')
    setMessage('')

    try {
        const res = await apiClient.post(
            `/service/${editingServiceId}/complete`
        )
        console.log('Manual complete service response:', res.data)

        setMessage('Service completed and car returned to inventory')
        setEditingServiceId(null)
        await fetchService()
    } catch (err) {
        console.error('Failed to complete service record:', err)
        if (err.response?.data?.detail) {
            setEditError(err.response.data.detail)
        } else {
            setEditError('Failed to complete service record')
        }
    }
}

return (
    <div>
        <h2>Service</h2>
        {message && <p>{message}</p>}

        {/* ---- Single (Quick) Service Entry ---- */}
        <div
            style={{
                marginBottom: '2rem',
                border: '1px solid #ccc',
                padding: '1rem',
            }}
        >
            <h3>Single Service Entry</h3>
            {simpleError && (
                <p style={{ color: 'red', marginBottom: '1rem' }}>{simpleError}</p>
            )}
            <form onSubmit={handleSimpleSubmit}>
                <div>
                    <label>VIN (required)</label>
                    <input
                        name="vin_number"
                        value={simpleForm.vin_number}
                        onChange={handleSimpleChange}
                        required
                    />
                </div>

                <div>
                    <label>Seriousness (required)</label>
                    <select
                        name="seriousness_level"
                        value={simpleForm.seriousness_level}
                        onChange={handleSimpleChange}
                        required
                    >
                        <option value="">Select...</option>
                        <option value="Low">Low</option>
                        <option value="Medium">Medium</option>
                        <option value="High">High</option>
                    </select>
                </div>

                <div>
                    <label>Estimated Days (optional)</label>
                    <input
                        type="number"
                        name="estimated_days"
                        value={simpleForm.estimated_days}
                        onChange={handleSimpleChange}
                    />
                </div>

                <div>
                    <label>Cost Added / Repair Cost (optional)</label>
                    <input
                        type="number"
                        name="cost_added"
                        value={simpleForm.cost_added}
                        onChange={handleSimpleChange}
                    />
                </div>

                <button type="submit">Add to Service</button>
            </form>
        </div>

        {/* ---- Service Table ---- */}
        <h3>Current Service Records</h3>
        <table border="1" cellPadding="4">
            <thead>
            <tr>
                <th>Service ID</th>
                <th>VIN</th>
                {/* Car info */}
                <th>Make</th>
                <th>Model</th>
                <th>Year</th>
                <th>Mileage</th>
                {/* Service details */}
                <th>Seriousness</th>
                <th>Estimated Days</th>
                <th>Repair Cost</th>
                <th>Service Start Date</th>
                <th>Actions</th>
            </tr>
            </thead>
            <tbody>
            {records.map((r) => (
                <tr key={r.id}>
                    <td>{r.service_id}</td>
                    <td>{r.vin_number}</td>
                    <td>{r.make}</td>
                    <td>{r.model}</td>
                    <td>{r.year}</td>
                    <td>{r.mileage}</td>
                    <td>{r.seriousness_level}</td>
                    <td>{r.estimated_days}</td>
                    <td>{r.cost_added}</td>
                    <td>{formatDate(r.service_start_date || r.created_at)}</td>
                    <td>
                        <button type="button" onClick={() => startEdit(r)}>
                            Edit
                        </button>
                    </td>
                </tr>
            ))}
            </tbody>
        </table>

        {/* ---- Edit Panel ---- */}
        {editingServiceId && (
            <div
                style={{
                    marginTop: '2rem',
                    border: '1px solid #ccc',
                    padding: '1rem',
                }}
            >
                <h3>Edit Service (ID: {editingServiceId})</h3>
                {editError && (
                    <p style={{ color: 'red', marginBottom: '1rem' }}>{editError}</p>
                )}
                <form onSubmit={handleUpdateService}>
                    <div>
                        <label>Seriousness</label>
                        <select
                            name="seriousness_level"
                            value={editForm.seriousness_level}
                            onChange={handleEditChange}
                            required
                        >
                            <option value="">Select...</option>
                            <option value="Low">Low</option>
                            <option value="Medium">Medium</option>
                            <option value="High">High</option>
                        </select>
                    </div>

                    <div>
                        <label>Estimated Days</label>
                        <input
                            type="number"
                            name="estimated_days"
                            value={editForm.estimated_days}
                            onChange={handleEditChange}
                            required
                        />
                    </div>

                    <div>
                        <label>Repair Cost</label>
                        <input
                            type="number"
                            name="cost_added"
                            value={editForm.cost_added}
                            onChange={handleEditChange}
                        />
                    </div>

                    <div>
                        <label>Service Start Date (MM/DD/YYYY)</label>
                        <input
                            name="service_start_date"
                            value={editForm.service_start_date}
                            onChange={handleEditChange}
                            required
                        />
                    </div>

                    <button type="submit">Save</button>

                    <button
                        type="button"
                        onClick={handleCompleteService}
                        style={{ marginLeft: '0.5rem' }}
                    >
                        Complete & Return to Inventory
                    </button>

                    <button
                        type="button"
                        onClick={cancelEdit}
                        style={{ marginLeft: '0.5rem' }}
                    >
                        Cancel
                    </button>
                </form>
            </div>
        )}
    </div>
)
}
