import { useState, useEffect } from 'react'
import { User } from 'firebase/auth'
import { onAuthChange, signOut } from '../services/firebaseConfig'

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const unsubscribe = onAuthChange((user) => {
      setUser(user)
      setLoading(false)
    })

    return () => unsubscribe()
  }, [])

  const logout = async () => {
    await signOut()
    setUser(null)
  }

  return { user, loading, logout }
}
