// frontend/src/pages/LoginPage.jsx
import React, { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { apiClient } from '../apiClient'

// Small helper to decode JWT payload without extra libraries
function decodeJwtPayload(token) {
    try {
        const [, payloadBase64] = token.split('.')
        const normalized = payloadBase64.replace(/-/g, '+').replace(/_/g, '/')
        const json = atob(normalized)
        return JSON.parse(json)
    } catch (e) {
        console.error('Failed to decode JWT payload', e)
        return {}
    }
}

export default function LoginPage() {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [message, setMessage] = useState('')

    const navigate = useNavigate()
    const location = useLocation()
    const from = location.state?.from?.pathname || '/home'

    const handleSubmit = async (e) => {
        e.preventDefault()
        setMessage('')

        try {
            const formData = new FormData()
            formData.append('username', username)
            formData.append('password', password)

            // Use baseURL from apiClient
            const res = await apiClient.post('/auth/login', formData)

            const token = res.data.access_token
            localStorage.setItem('token', token)

            // Decode token to pull role & location
            const payload = decodeJwtPayload(token)
            const jwtUsername = payload.sub || username
            const jwtRole = payload.role || ''
            const jwtLocation = payload.location || ''

            localStorage.setItem('username', jwtUsername)
            localStorage.setItem('role', jwtRole)         // <— important
            localStorage.setItem('location', jwtLocation) // <— important

            setMessage('Logged in!')

            // Go to where they were heading, or /home
            navigate(from, { replace: true })
        } catch (err) {
            console.error('Login failed', err)
            setMessage('Login failed')
            // Clear any old auth data
            localStorage.removeItem('token')
            localStorage.removeItem('role')
            localStorage.removeItem('username')
            localStorage.removeItem('location')
        }
    }

    return (
        <div>
            <h2>Login</h2>
            <form onSubmit={handleSubmit}>
                <div>
                    <label>Username</label>
                    <input
                        value={username}
                        onChange={e => setUsername(e.target.value)}
                    />
                </div>
                <div>
                    <label>Password</label>
                    <input
                        type="password"
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                    />
                </div>
                <button type="submit">Login</button>
            </form>
            {message && <p>{message}</p>}
        </div>
    )
}
