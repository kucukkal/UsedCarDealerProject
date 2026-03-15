// frontend/src/pages/AdminPage.jsx
import React, { useState } from 'react'
import { apiClient } from '../apiClient'

export default function AdminPage() {
    const [form, setForm] = useState({
        username: '',
        password: '',
        role: 'SalesRep',   // default role
        location: 'Denver', // default location – adjust to your locations
    })

    const [message, setMessage] = useState('')
    const [error, setError] = useState('')

    const currentRole = localStorage.getItem('role')
    const currentUser = localStorage.getItem('username')
    const currentLocation = localStorage.getItem('location')

    // Simple client-side guard (backend should ALSO enforce Admin-only)
    if (currentRole !== 'Admin') {
        return (
            <div>
                <h2>Admin Page</h2>
                <p style={{ color: 'red' }}>
                    You do not have permission to view this page.
                </p>
            </div>
        )
    }

    const handleChange = (e) => {
        const { name, value } = e.target
        setForm((prev) => ({ ...prev, [name]: value }))
        setError('')
        setMessage('')
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setMessage('')

        if (!form.username.trim()) {
            setError('Username is required.')
            return
        }
        if (!form.password) {
            setError('Password is required.')
            return
        }
        if (!form.role.trim()) {
            setError('Role is required.')
            return
        }
        if (!form.location.trim()) {
            setError('Location is required.')
            return
        }

        const payload = {
            username: form.username.trim(),
            password: form.password,
            role: form.role,
            location: form.location,
        }

        try {
            await apiClient.post('/auth/create-user', payload)
            setMessage(`User "${payload.username}" created successfully.`)
            // Optionally clear the form (except maybe role/location)
            setForm((prev) => ({
                ...prev,
                username: '',
                password: '',
            }))
        } catch (err) {
            console.error('Failed to create user', err)
            if (err.response?.data?.detail) {
                setError(err.response.data.detail)
            } else {
                setError('Failed to create user.')
            }
        }
    }

    return (
        <div>
            <h2>Admin Tools – User Management</h2>
            <p style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
                Logged in as <strong>{currentUser}</strong> ({currentRole}) at{' '}
                <strong>{currentLocation}</strong>
            </p>

            <section style={{ border: '1px solid #ccc', padding: '1rem', maxWidth: '450px' }}>
                <h3>Create New User</h3>

                {error && <p style={{ color: 'red' }}>{error}</p>}
                {message && <p style={{ color: 'green' }}>{message}</p>}

                <form onSubmit={handleSubmit}>
                    <div style={{ marginBottom: '0.75rem' }}>
                        <label>Username (required)</label>
                        <br />
                        <input
                            type="text"
                            name="username"
                            value={form.username}
                            onChange={handleChange}
                            style={{ width: '100%' }}
                        />
                    </div>

                    <div style={{ marginBottom: '0.75rem' }}>
                        <label>Password (required)</label>
                        <br />
                        <input
                            type="password"
                            name="password"
                            value={form.password}
                            onChange={handleChange}
                            style={{ width: '100%' }}
                        />
                    </div>

                    <div style={{ marginBottom: '0.75rem' }}>
                        <label>Role (required)</label>
                        <br />
                        <select
                            name="role"
                            value={form.role}
                            onChange={handleChange}
                            style={{ width: '100%' }}
                        >
                            <option value="Admin">Admin</option>
                            <option value="PR">PR</option>
                            <option value="ServiceRep">ServiceRep</option>
                            <option value="SalesRep">SalesRep</option>
                            <option value="Finance">Finance</option>
                            <option value="BuyerRep">BuyerRep</option>
                        </select>
                    </div>

                    <div style={{ marginBottom: '0.75rem' }}>
                        <label>Location (required)</label>
                        <br />
                        <input
                            type="text"
                            name="location"
                            value={form.location}
                            onChange={handleChange}
                            style={{ width: '100%' }}
                            placeholder="e.g. Denver, New York"
                        />
                    </div>

                    <button type="submit">Create User</button>
                </form>
            </section>
        </div>
    )
}
