import { initializeApp, getApps, FirebaseApp } from 'firebase/app'
import { 
  getAuth, 
  signInWithEmailAndPassword, 
  signInWithPopup, 
  GoogleAuthProvider,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  User,
  Auth
} from 'firebase/auth'

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
}

const missingFirebaseVars = Object.entries(firebaseConfig)
  .filter(([, value]) => !value)
  .map(([key]) => key)

if (missingFirebaseVars.length > 0) {
  throw new Error(
    `Missing Firebase environment variables: ${missingFirebaseVars.join(', ')}. ` +
    `Create a .env file from .env.example and restart the dev server.`,
  )
}

// Initialize Firebase
let app: FirebaseApp
if (!getApps().length) {
  app = initializeApp(firebaseConfig)
} else {
  app = getApps()[0]
}

export const auth: Auth = getAuth(app)
export const googleProvider = new GoogleAuthProvider()

const FIREBASE_TOKEN_KEY = 'firebase_token'
const FIREBASE_REFRESH_TOKEN_KEY = 'firebase_refresh_token'

const persistAuthTokens = async (user: User | null) => {
  if (!user) {
    localStorage.removeItem(FIREBASE_TOKEN_KEY)
    localStorage.removeItem(FIREBASE_REFRESH_TOKEN_KEY)
    return null
  }

  const token = await user.getIdToken()
  localStorage.setItem(FIREBASE_TOKEN_KEY, token)
  localStorage.setItem(FIREBASE_REFRESH_TOKEN_KEY, user.refreshToken)
  return token
}

// Auth functions
export const signInWithEmail = async (email: string, password: string) => {
  const result = await signInWithEmailAndPassword(auth, email, password)
  await persistAuthTokens(result.user)
  return result.user
}

export const signUpWithEmail = async (email: string, password: string) => {
  const result = await createUserWithEmailAndPassword(auth, email, password)
  await persistAuthTokens(result.user)
  return result.user
}

export const signInWithGoogle = async () => {
  const result = await signInWithPopup(auth, googleProvider)
  await persistAuthTokens(result.user)
  return result.user
}

export const signOut = async () => {
  await firebaseSignOut(auth)
  localStorage.removeItem(FIREBASE_TOKEN_KEY)
  localStorage.removeItem(FIREBASE_REFRESH_TOKEN_KEY)
}

export const onAuthChange = (callback: (user: User | null) => void) => {
  return onAuthStateChanged(auth, async (user) => {
    try {
      await persistAuthTokens(user)
    } finally {
      callback(user)
    }
  })
}

export const getAuthToken = async () => {
  if (auth.currentUser) {
    return persistAuthTokens(auth.currentUser)
  }
  return localStorage.getItem(FIREBASE_TOKEN_KEY)
}

export default app
