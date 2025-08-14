'use client'

import { useState, useEffect } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

interface AuthStatus {
  authenticated: boolean
  cloud_id?: string
  account_id?: string
  expires_at?: string
  message?: string
}

export default function Home() {
  const [result, setResult] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [authStatus, setAuthStatus] = useState<AuthStatus>({ authenticated: false })
  const [cloudId, setCloudId] = useState<string>('')

  useEffect(() => {
    // Check for OAuth callback success/error
    const urlParams = new URLSearchParams(window.location.search)
    const authResult = urlParams.get('auth')
    const cloudIdParam = urlParams.get('cloud_id')
    
    if (authResult === 'success' && cloudIdParam) {
      setCloudId(cloudIdParam)
      setResult(`🎉 Jira authentication successful! Cloud ID: ${cloudIdParam}`)
      // Clear URL parameters
      window.history.replaceState({}, document.title, window.location.pathname)
    } else if (authResult === 'error') {
      const message = urlParams.get('message') || 'Authentication failed'
      setResult(`❌ Authentication failed: ${message}`)
      // Clear URL parameters
      window.history.replaceState({}, document.title, window.location.pathname)
    }
  }, [])

  useEffect(() => {
    // Check auth status when cloudId changes
    if (cloudId) {
      checkAuthStatus()
    }
  }, [cloudId])

  const checkAuthStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/auth/status?cloud_id=${cloudId}`)
      const data = await response.json()
      setAuthStatus(data)
    } catch (error) {
      console.error('Auth status check failed:', error)
    }
  }

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

  const startJiraAuth = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/auth/jira/login`)
      const data = await response.json()
      // Redirect to Jira OAuth
      window.location.href = data.authorization_url
    } catch (error) {
      setResult(`OAuth Error: ${error}`)
      setLoading(false)
    }
  }

  const callAuthenticatedAPI = async (endpoint: string) => {
    if (!authStatus.authenticated || !authStatus.account_id) {
      setResult('❌ Please authenticate with Jira first')
      return
    }
    
    const accountId = authStatus.account_id
    const url = endpoint.includes('?') 
      ? `${endpoint}&accountId=${accountId}`
      : `${endpoint}?accountId=${accountId}`
    
    await callAPI(url)
  }

  return (
    <div className="min-h-screen p-8 bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            🤖 AI Scrum Master MVP
          </h1>
          <p className="text-xl text-gray-600 mb-6">
            Intelligent Agile Automation Platform
          </p>
          
          {/* Auth Status */}
          <div className="bg-white rounded-lg shadow-md p-4 mb-6 max-w-md mx-auto">
            <h3 className="font-semibold mb-2">Authentication Status</h3>
            {authStatus.authenticated ? (
              <div className="text-green-600">
                ✅ Connected to Jira
                <div className="text-sm text-gray-600 mt-1">
                  Account: {authStatus.account_id}
                </div>
              </div>
            ) : (
              <div className="text-red-600">
                ❌ Not connected to Jira
                <div className="text-sm text-gray-600 mt-1">
                  Connect to use AI features
                </div>
              </div>
            )}
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {/* Basic Endpoints */}
          <button
            onClick={() => callAPI('/healthz')}
            disabled={loading}
            className="bg-green-500 hover:bg-green-600 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 shadow-md"
          >
            Health Check
          </button>
          
          <button
            onClick={() => callAPI('/metrics')}
            disabled={loading}
            className="bg-purple-500 hover:bg-purple-600 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 shadow-md"
          >
            📊 Metrics
          </button>
          
          <button
            onClick={() => callAPI('/insights/sprint?boardId=demo&accountId=demo')}
            disabled={loading}
            className="bg-indigo-500 hover:bg-indigo-600 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 shadow-md"
          >
            📈 Sprint Insights
          </button>
          
          {/* Auth Button */}
          <button
            onClick={startJiraAuth}
            disabled={loading}
            className="bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 shadow-md"
          >
            🔗 Connect Jira
          </button>
        </div>

        {/* AI-Powered Features */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-2xl font-bold mb-4 text-center">🧠 AI-Powered Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => callAuthenticatedAPI('/summarize/standup')}
              disabled={loading}
              className="bg-orange-500 hover:bg-orange-600 text-white font-semibold py-4 px-6 rounded-lg disabled:opacity-50 shadow-md"
            >
              📋 AI Standup Summary
            </button>
            
            <button
              onClick={() => callAuthenticatedAPI('/summarize/blockers')}
              disabled={loading}
              className="bg-red-500 hover:bg-red-600 text-white font-semibold py-4 px-6 rounded-lg disabled:opacity-50 shadow-md"
            >
              🚫 AI Blocker Analysis
            </button>
            
            <button
              onClick={() => callAPI('/summarize/retrospective?boardId=demo&sprintId=123')}
              disabled={loading}
              className="bg-teal-500 hover:bg-teal-600 text-white font-semibold py-4 px-6 rounded-lg disabled:opacity-50 shadow-md"
            >
              🔄 AI Retrospective
            </button>
          </div>
          
          {!authStatus.authenticated && (
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-yellow-800 text-sm">
                💡 <strong>Tip:</strong> Connect to Jira to unlock personalized AI insights for your team's work!
              </p>
            </div>
          )}
        </div>

        {/* Loading Indicator */}
        {loading && (
          <div className="flex justify-center py-8">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        )}

        {/* Results Display */}
        {result && (
          <div className="bg-gray-900 text-green-400 p-6 rounded-lg overflow-auto shadow-lg">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-white">API Response</h3>
              <button
                onClick={() => setResult('')}
                className="text-gray-400 hover:text-white"
              >
                ✕ Clear
              </button>
            </div>
            <pre className="whitespace-pre-wrap text-sm">{result}</pre>
          </div>
        )}

        {/* Features Info */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-8 text-center">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-bold mb-3">🔐 OAuth Integration</h3>
            <p className="text-gray-600">
              Secure Jira authentication with OAuth 2.0 PKCE flow for accessing your team's data
            </p>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-bold mb-3">📊 Real-time Insights</h3>
            <p className="text-gray-600">
              Get instant sprint metrics, burndown charts, and team performance analytics
            </p>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-bold mb-3">🤖 AI-Powered Summaries</h3>
            <p className="text-gray-600">
              Automated standup reports, blocker identification, and retrospective insights
            </p>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-bold mb-3">⚡ Production Ready</h3>
            <p className="text-gray-600">
              Built with FastAPI, PostgreSQL, Redis, and comprehensive monitoring
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}