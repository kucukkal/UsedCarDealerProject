// frontend/src/pages/InventoryPage.jsx
import React, { useEffect, useState } from 'react'
import { apiClient } from '../apiClient'

export default function InventoryPage() {
    const [cars, setCars] = useState([])
    const [message, setMessage] = useState('')
    const [excelFile, setExcelFile] = useState(null)

    const [singleEntryError, setSingleEntryError] = useState('')
    const [excelUploadError, setExcelUploadError] = useState('')
    const [editError, setEditError] = useState('')

    const role = localStorage.getItem('role')
    const userLocation = localStorage.getItem('location') || ''

    // CREATE FORM (updated with new inventory fields)
    const [form, setForm] = useState({
        make: '',
        model: '',
        sub_model: '',
        year: '',
        mileage: '',
        vehicle_type: '',
        color: '',
        antique: '', // UI input -> convert to boolean or null on submit
        condition_type: '',
        cost: '',
        sale_price: '',
        location: role === 'BuyerRep' ? userLocation : '',
    })

    // EDIT STATE
    const [editingVin, setEditingVin] = useState(null)
    const [editForm, setEditForm] = useState({
        make: '',
        model: '',
        sub_model: '',
        year: '',
        mileage: '',
        vehicle_type: '',
        color: '',
        antique: '', // UI input -> convert to boolean or null on submit
        condition_type: '',
        cost: '',
        sale_price: '',
        location: '',
        status: '',
    })

    const fetchCars = async () => {
        try {
            const res = await apiClient.get('/inventory/')
            setCars(res.data || [])
        } catch (err) {
            console.error('Failed to load inventory:', err)
        }
    }

    useEffect(() => {
        fetchCars()
    }, [])

    const handleFormChange = (e) => {
        const { name, value } = e.target
        setForm((prev) => ({ ...prev, [name]: value }))
    }

    const normalizeAntique = (val) => {
        // Accept: "true" | "false" | "" (empty)
        if (val === '' || val === null || val === undefined) return null
        if (val === true || val === false) return val
        if (typeof val === 'string') {
            const v = val.trim().toLowerCase()
            if (v === 'true' || v === 'yes') return true
            if (v === 'false' || v === 'no') return false
        }
        return null
    }

    const handleCreateCar = async (e) => {
        e.preventDefault()
        setMessage('')
        setSingleEntryError('')

        try {
            const payload = {
                make: form.make,
                model: form.model,
                sub_model: form.sub_model || null,
                vehicle_type: form.vehicle_type || null,
                color: form.color || null,
                antique: normalizeAntique(form.antique),
                condition_type: form.condition_type,
                year: Number(form.year),
                mileage: Number(form.mileage),
                cost: Number(form.cost),
                sale_price: Number(form.sale_price),
                location: form.location,
            }

            if (role === 'BuyerRep') {
                payload.location = userLocation
            }

            const res = await apiClient.post('/inventory/', payload)
            console.log('Create car response:', res.data)

            setMessage('Car added to inventory')

            setForm({
                make: '',
                model: '',
                sub_model: '',
                year: '',
                mileage: '',
                vehicle_type: '',
                color: '',
                antique: '',
                condition_type: '',
                cost: '',
                sale_price: '',
                location: role === 'BuyerRep' ? userLocation : '',
            })

            await fetchCars()
        } catch (err) {
            console.error('Failed to add car:', err)
            if (err.response && err.response.data && err.response.data.detail) {
                setSingleEntryError(err.response.data.detail)
            } else {
                setSingleEntryError('Failed to add car')
            }
        }
    }

    const handleExcelChange = (e) => {
        setExcelFile(e.target.files[0] || null)
    }

    const handleExcelUpload = async (e) => {
        e.preventDefault()
        setMessage('')
        setExcelUploadError('')

        if (!excelFile) {
            setExcelUploadError('Please select a file first')
            return
        }

        try {
            const data = new FormData()
            data.append('file', excelFile)

            console.log('Uploading file:', excelFile.name)

            const res = await apiClient.post('/inventory/upload', data)
            console.log('Upload response:', res.data)

            if (res.data && res.data.detail) {
                setMessage(res.data.detail)
            } else {
                setMessage('Excel file uploaded.')
            }

            setExcelFile(null)
            await fetchCars()
        } catch (err) {
            console.error('Failed to upload Excel file:', err)
            if (err.response && err.response.data && err.response.data.detail) {
                setExcelUploadError(err.response.data.detail)
            } else {
                setExcelUploadError('Failed to upload Excel file')
            }
        }
    }

    const canEdit = role === 'Admin' || role === 'BuyerRep'

    // ------- EDIT HANDLERS -------

    const startEdit = (car) => {
        setEditingVin(car.vin_number)
        setEditForm({
            make: car.make || '',
            model: car.model || '',
            sub_model: car.sub_model || '',
            year: String(car.year ?? ''),
            mileage: String(car.mileage ?? ''),
            vehicle_type: car.vehicle_type || '',
            color: car.color || '',
            antique:
                car.antique === true ? 'true' : car.antique === false ? 'false' : '',
            condition_type: car.condition_type || '',
            cost: String(car.cost ?? ''),
            sale_price: String(car.sale_price ?? ''),
            location: car.location || '',
            status: car.status || '',
        })
        setMessage('')
        setEditError('')
    }

    const handleEditChange = (e) => {
        const { name, value } = e.target
        setEditForm((prev) => ({ ...prev, [name]: value }))
    }

    const cancelEdit = () => {
        setEditingVin(null)
        setEditForm({
            make: '',
            model: '',
            sub_model: '',
            year: '',
            mileage: '',
            vehicle_type: '',
            color: '',
            antique: '',
            condition_type: '',
            cost: '',
            sale_price: '',
            location: '',
            status: '',
        })
        setEditError('')
    }

    const handleUpdateCar = async (e) => {
        e.preventDefault()
        if (!editingVin) return

        setMessage('')
        setEditError('')

        try {
            const payload = {
                make: editForm.make,
                model: editForm.model,
                sub_model: editForm.sub_model || null,
                vehicle_type: editForm.vehicle_type || null,
                color: editForm.color || null,
                antique: normalizeAntique(editForm.antique),
                year: Number(editForm.year),
                mileage: Number(editForm.mileage),
                condition_type: editForm.condition_type,
                cost: Number(editForm.cost),
                sale_price: Number(editForm.sale_price),
                status: editForm.status,
            }

            if (role === 'BuyerRep') {
                payload.location = userLocation
            } else {
                payload.location = editForm.location
            }

            const res = await apiClient.patch(`/inventory/${editingVin}`, payload)
            console.log('Update car response:', res.data)

            setMessage('Car updated successfully')
            setEditingVin(null)
            await fetchCars()
        } catch (err) {
            console.error('Failed to update car:', err)
            if (err.response && err.response.data && err.response.data.detail) {
                setEditError(err.response.data.detail)
            } else {
                setEditError('Failed to update car')
            }
        }
    }

    return (
        <div>
            <h2>Inventory</h2>

            {message && <p>{message}</p>}

            {/* Admin & BuyerRep: Single-car and Excel upload */}
            {canEdit && (
                <div
                    style={{
                        marginBottom: '2rem',
                        border: '1px solid #ccc',
                        padding: '1rem',
                    }}
                >
                    <h3>Single Car Entry</h3>

                    {singleEntryError && (
                        <p style={{ color: 'red', marginBottom: '1rem' }}>
                            {singleEntryError}
                        </p>
                    )}

                    <form onSubmit={handleCreateCar}>
                        <div>
                            <label>Make</label>
                            <input
                                name="make"
                                value={form.make}
                                onChange={handleFormChange}
                                required
                            />
                        </div>

                        <div>
                            <label>Model</label>
                            <input
                                name="model"
                                value={form.model}
                                onChange={handleFormChange}
                                required
                            />
                        </div>

                        <div>
                            <label>SubModel</label>
                            <input
                                name="sub_model"
                                value={form.sub_model}
                                onChange={handleFormChange}
                                placeholder="Optional"
                            />
                        </div>

                        <div>
                            <label>Year</label>
                            <input
                                type="number"
                                name="year"
                                value={form.year}
                                onChange={handleFormChange}
                                required
                            />
                        </div>

                        <div>
                            <label>Mileage</label>
                            <input
                                type="number"
                                name="mileage"
                                value={form.mileage}
                                onChange={handleFormChange}
                                required
                            />
                        </div>

                        <div>
                            <label>Type</label>
                            <input
                                name="vehicle_type"
                                value={form.vehicle_type}
                                onChange={handleFormChange}
                                placeholder="SUV, Sedan, Truck..."
                            />
                        </div>

                        <div>
                            <label>Color</label>
                            <input
                                name="color"
                                value={form.color}
                                onChange={handleFormChange}
                                placeholder="Optional"
                            />
                        </div>

                        <div>
                            <label>Antique</label>
                            <select
                                name="antique"
                                value={form.antique}
                                onChange={handleFormChange}
                            >
                                <option value="">(Auto/Unknown)</option>
                                <option value="false">No</option>
                                <option value="true">Yes</option>
                            </select>
                            <small style={{ display: 'block' }}>
                                If blank, backend may compute it based on age if you enforce that rule.
                            </small>
                        </div>

                        <div>
                            <label>Condition</label>
                            <select
                                name="condition_type"
                                value={form.condition_type}
                                onChange={handleFormChange}
                                required
                            >
                                <option value="">Select...</option>
                                <option value="Damaged">Damaged</option>
                                <option value="Good">Good</option>
                                <option value="Mint">Mint</option>
                                <option value="Like New">Like New</option>
                            </select>
                        </div>

                        <div>
                            <label>Cost</label>
                            <input
                                type="number"
                                name="cost"
                                value={form.cost}
                                onChange={handleFormChange}
                                required
                            />
                        </div>

                        <div>
                            <label>Sale Price</label>
                            <input
                                type="number"
                                name="sale_price"
                                value={form.sale_price}
                                onChange={handleFormChange}
                                required
                            />
                        </div>

                        <div>
                            <label>Location</label>
                            {role === 'BuyerRep' ? (
                                <>
                                    <input name="location" value={userLocation} readOnly />
                                    <small>Buyer reps use their own location only.</small>
                                </>
                            ) : (
                                <input
                                    name="location"
                                    value={form.location}
                                    onChange={handleFormChange}
                                    required
                                />
                            )}
                        </div>

                        <button type="submit">Add Car</button>
                    </form>

                    <hr style={{ margin: '1.5rem 0' }} />

                    <h3>Excel Upload (Batch)</h3>

                    {excelUploadError && (
                        <p style={{ color: 'red', marginBottom: '1rem' }}>
                            {excelUploadError}
                        </p>
                    )}

                    <form onSubmit={handleExcelUpload}>
                        <div>
                            <input
                                type="file"
                                accept=".xlsx,.xls"
                                onChange={handleExcelChange}
                            />
                        </div>
                        <button type="submit">Upload Inventory File</button>
                    </form>
                </div>
            )}

            <h3>Current Inventory</h3>
            <table border="1" cellPadding="4">
                <thead>
                <tr>
                    <th>VIN</th>
                    <th>Make</th>
                    <th>Model</th>
                    <th>SubModel</th>
                    <th>Year</th>
                    <th>Mileage</th>
                    <th>Type</th>
                    <th>Color</th>
                    <th>Antique</th>
                    <th>Condition</th>
                    <th>Cost</th>
                    <th>Sale Price</th>
                    <th>Status</th>
                    <th>Location</th>
                    {canEdit && <th>Actions</th>}
                </tr>
                </thead>
                <tbody>
                {cars.map((c) => (
                    <tr key={c.id}>
                        <td>{c.vin_number}</td>
                        <td>{c.make}</td>
                        <td>{c.model}</td>
                        <td>{c.sub_model || ''}</td>
                        <td>{c.year}</td>
                        <td>{c.mileage}</td>
                        <td>{c.vehicle_type || ''}</td>
                        <td>{c.color || ''}</td>
                        <td>
                            {c.antique === true ? 'Yes' : c.antique === false ? 'No' : ''}
                        </td>
                        <td>{c.condition_type}</td>
                        <td>{c.cost}</td>
                        <td>{c.sale_price}</td>
                        <td>{c.status}</td>
                        <td>{c.location}</td>
                        {canEdit && (
                            <td>
                                <button type="button" onClick={() => startEdit(c)}>
                                    Edit
                                </button>
                            </td>
                        )}
                    </tr>
                ))}
                </tbody>
            </table>

            {canEdit && editingVin && (
                <div
                    style={{
                        marginTop: '2rem',
                        border: '1px solid #ccc',
                        padding: '1rem',
                    }}
                >
                    <h3>Edit Car (VIN: {editingVin})</h3>

                    {editError && (
                        <p style={{ color: 'red', marginBottom: '1rem' }}>{editError}</p>
                    )}

                    <form onSubmit={handleUpdateCar}>
                        <div>
                            <label>Make</label>
                            <input
                                name="make"
                                value={editForm.make}
                                onChange={handleEditChange}
                                required
                            />
                        </div>

                        <div>
                            <label>Model</label>
                            <input
                                name="model"
                                value={editForm.model}
                                onChange={handleEditChange}
                                required
                            />
                        </div>

                        <div>
                            <label>SubModel</label>
                            <input
                                name="sub_model"
                                value={editForm.sub_model}
                                onChange={handleEditChange}
                                placeholder="Optional"
                            />
                        </div>

                        <div>
                            <label>Year</label>
                            <input
                                type="number"
                                name="year"
                                value={editForm.year}
                                onChange={handleEditChange}
                                required
                            />
                        </div>

                        <div>
                            <label>Mileage</label>
                            <input
                                type="number"
                                name="mileage"
                                value={editForm.mileage}
                                onChange={handleEditChange}
                                required
                            />
                        </div>

                        <div>
                            <label>Type</label>
                            <input
                                name="vehicle_type"
                                value={editForm.vehicle_type}
                                onChange={handleEditChange}
                                placeholder="SUV, Sedan, Truck..."
                            />
                        </div>

                        <div>
                            <label>Color</label>
                            <input
                                name="color"
                                value={editForm.color}
                                onChange={handleEditChange}
                                placeholder="Optional"
                            />
                        </div>

                        <div>
                            <label>Antique</label>
                            <select
                                name="antique"
                                value={editForm.antique}
                                onChange={handleEditChange}
                            >
                                <option value="">(Auto/Unknown)</option>
                                <option value="false">No</option>
                                <option value="true">Yes</option>
                            </select>
                        </div>

                        <div>
                            <label>Condition</label>
                            <select
                                name="condition_type"
                                value={editForm.condition_type}
                                onChange={handleEditChange}
                                required
                            >
                                <option value="">Select...</option>
                                <option value="Damaged">Damaged</option>
                                <option value="Good">Good</option>
                                <option value="Mint">Mint</option>
                                <option value="Like New">Like New</option>
                            </select>
                        </div>

                        <div>
                            <label>Cost</label>
                            <input
                                type="number"
                                name="cost"
                                value={editForm.cost}
                                onChange={handleEditChange}
                                required
                            />
                        </div>

                        <div>
                            <label>Sale Price</label>
                            <input
                                type="number"
                                name="sale_price"
                                value={editForm.sale_price}
                                onChange={handleEditChange}
                                required
                            />
                        </div>

                        <div>
                            <label>Status</label>
                            <input
                                name="status"
                                value={editForm.status}
                                onChange={handleEditChange}
                            />
                        </div>

                        <div>
                            <label>Location</label>
                            {role === 'BuyerRep' ? (
                                <>
                                    <input name="location" value={userLocation} readOnly />
                                    <small>Buyer reps use their own location only.</small>
                                </>
                            ) : (
                                <input
                                    name="location"
                                    value={editForm.location}
                                    onChange={handleEditChange}
                                    required
                                />
                            )}
                        </div>

                        <button type="submit">Save Changes</button>
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
