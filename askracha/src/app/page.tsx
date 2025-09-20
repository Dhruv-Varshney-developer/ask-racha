"use client"

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function Home() {
  const router = useRouter()

  useEffect(() => {
    const existingSessionId = typeof window !== 'undefined' 
      ? localStorage.getItem('askracha-session-id')
      : null

    if (existingSessionId) {
      router.replace(`/chat/${existingSessionId}`)
    } else {
      router.replace('/chat')
    }
  }, [])

  return null
}
