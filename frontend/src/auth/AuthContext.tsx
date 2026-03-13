import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface AuthUser {
  username: string
  role: string
  token: string
}

interface AuthContextType {
  user: AuthUser | null
  login: (username: string, token: string, role: string) => void
  logout: () => void
  isAdmin: boolean
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  login: () => {},
  logout: () => {},
  isAdmin: false,
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    try {
      const stored = localStorage.getItem('ha_user')
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })

  useEffect(() => {
    if (user) localStorage.setItem('ha_user', JSON.stringify(user))
    else localStorage.removeItem('ha_user')
  }, [user])

  const login = (username: string, token: string, role: string) => {
    setUser({ username, token, role })
  }

  const logout = () => setUser(null)

  return (
    <AuthContext.Provider value={{ user, login, logout, isAdmin: user?.role === 'admin' }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
