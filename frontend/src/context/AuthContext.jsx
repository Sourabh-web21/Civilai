import { createContext, useContext, useState, useCallback } from 'react'
import { api, unwrap, errMessage } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('civilai_user') || 'null')
    } catch {
      return null
    }
  })

  const login = useCallback(async (email, password) => {
    try {
      const res = await api.post('/api/v1/user/login', { email, password })
      const data = unwrap(res) // object: { email, full_name, id, tokens: { access_token } }
      const token = data?.tokens?.access_token
      if (!token) throw new Error('No token returned')
      const profile = {
        id: data.id,
        email: data.email,
        full_name: data.full_name || data.email,
      }
      localStorage.setItem('civilai_token', token)
      localStorage.setItem('civilai_user', JSON.stringify(profile))
      setUser(profile)
      return { ok: true }
    } catch (err) {
      return { ok: false, error: errMessage(err) }
    }
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('civilai_token')
    localStorage.removeItem('civilai_user')
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthed: !!user }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
