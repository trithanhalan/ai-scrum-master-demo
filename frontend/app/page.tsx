'use client'

import { useState } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Home() {
  const [result, setResult] = useState<string>('')
  const [loading, setLoading] = useState(false)

  const callAPI = async (endpoint: string) => {
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}${endpoint}`)
      const data = await response.json()
      setResult(JSON.stringify(data, null, 2))
    } catch (error) {
      setResult(`Error: ${error}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">
          AI Scrum Master MVP
        </h1>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <button
            onClick={() => callAPI('/healthz')}
            disabled={loading}
            className="bg-green-500 hover:bg-green-600 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50"
          >
            Health Check
          </button>
          
          <button
            onClick={() => callAPI('/summarize/standup?accountId=demo')}
            disabled={loading}
            className="bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50"
          >
            Standup Summary
          </button>
          
          <button
            onClick={() => callAPI('/insights/sprint?boardId=demo&accountId=demo')}
            disabled={loading}
            className="bg-purple-500 hover:bg-purple-600 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50"
          >
            Sprint Insights
          </button>
        </div>

        {loading && (
          <div className="text-center py-4">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        )}

        {result && (
          <div className="bg-gray-800 text-green-400 p-4 rounded-lg overflow-auto">
            <pre>{result}</pre>
          </div>
        )}
      </div>
    </div>
  )
}