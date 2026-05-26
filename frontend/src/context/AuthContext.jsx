import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { login as apiLogin } from '../api/auth'
import { usersApi } from '../api/users'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadUser = useCallback(async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setLoading(false)
      return
    }
    try {
      const userData = await usersApi.me()
      setUser(userData)
    } catch {
      localStorage.removeItem('access_token')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadUser() }, [loadUser])

  const login = useCallback(async (email, password) => {
    const { access_token } = await apiLogin(email, password)
    localStorage.setItem('access_token', access_token)
    const userData = await usersApi.me()
    setUser(userData)
    return userData
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    setUser(null)
  }, [])

  const refreshUser = useCallback(async () => {
    const userData = await usersApi.me()
    setUser(userData)
    return userData
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
