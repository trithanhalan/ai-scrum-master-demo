'use client'

import { useState, useEffect } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

interface Connection {
  authenticated: boolean
  connection_id?: number
  account_id?: string
  cloud_id?: string
  display_name?: string
  email?: string
  expires_at?: string
  message?: string
}

// Helper function to make API calls with proper /api prefix
const makeAPICall = async (endpoint: string, options?: RequestInit) => {
  const url = `${API_URL}${endpoint.startsWith('/api') ? '' : '/api'}${endpoint}`
  return fetch(url, {
    credentials: 'include',
    ...options
  })
}

export default function Home() {
  const [result, setResult] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [connection, setConnection] = useState<Connection>({ authenticated: false })
  const [checkingConnection, setCheckingConnection] = useState(true)

  // Check connection status on component mount and after auth
  const checkConnection = async () => {
    try {
      const response = await makeAPICall('/auth/connection')
      const data = await response.json()
      setConnection(data)
      
      // Store in localStorage for persistence
      if (data.authenticated) {
        localStorage.setItem('jira_connection', JSON.stringify({
          account_id: data.account_id,
          cloud_id: data.cloud_id,
          display_name: data.display_name,
          connection_id: data.connection_id
        }))
      } else {
        localStorage.removeItem('jira_connection')
      }
    } catch (error) {
      console.error('Connection check failed:', error)
      setConnection({ authenticated: false, message: 'Connection check failed' })
    } finally {
      setCheckingConnection(false)
    }
  }

  useEffect(() => {
    // Check for OAuth callback success/error
    const urlParams = new URLSearchParams(window.location.search)
    const authResult = urlParams.get('auth')
    const cloudIdParam = urlParams.get('cloud_id')
    const accountIdParam = urlParams.get('account_id')
    
    if (authResult === 'success' && cloudIdParam && accountIdParam) {
      setResult(`🎉 Jira authentication successful!\n\nAccount: ${accountIdParam}\nCloud: ${cloudIdParam}`)
      // Clear URL parameters
      window.history.replaceState({}, document.title, window.location.pathname)
      // Check connection to get full details
      setTimeout(checkConnection, 1000)
    } else if (authResult === 'error') {
      const message = decodeURIComponent(urlParams.get('message') || 'Authentication failed')
      setResult(`❌ Authentication failed: ${message}`)
      // Clear URL parameters
      window.history.replaceState({}, document.title, window.location.pathname)
      setCheckingConnection(false)
    } else {
      // Normal page load - check existing connection
      checkConnection()
    }
  }, [])

  const callAPI = async (endpoint: string) => {
    setLoading(true)
    try {
      const response = await makeAPICall(endpoint)
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
      const response = await makeAPICall('/auth/jira/login')
      const data = await response.json()
      // Redirect to Jira OAuth
      if (data.authorization_url) {
        window.location.href = data.authorization_url
      } else {
        throw new Error('No authorization URL received')
      }
    } catch (error) {
      setResult(`OAuth Error: ${error}`)
      setLoading(false)
    }
  }

  const logout = async () => {
    setLoading(true)
    try {
      await fetch(`${API_URL}/auth/logout`, { 
        method: 'POST',
        credentials: 'include'
      })
      setConnection({ authenticated: false })
      localStorage.removeItem('jira_connection')
      setResult('Successfully logged out')
    } catch (error) {
      setResult(`Logout error: ${error}`)
    } finally {
      setLoading(false)
    }
  }

  const callAuthenticatedAPI = async (endpoint: string) => {
    if (!connection.authenticated) {
      setResult('❌ Please authenticate with Jira first to use AI features')
      return
    }
    
    // The backend will automatically use the session cookie to identify the user
    // No need to manually add account/cloud parameters
    await callAPI(endpoint)
  }

  if (checkingConnection) {
    return (
      <div className="min-h-screen p-8 bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
          <p className="text-gray-600">Checking connection status...</p>
        </div>
      </div>
    )
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
          
          {/* Connection Status */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6 max-w-md mx-auto">
            <h3 className="font-semibold mb-3">🔗 Jira Connection</h3>
            {connection.authenticated ? (
              <div className="text-green-600">
                <div className="flex items-center justify-center mb-2">
                  <span className="w-3 h-3 bg-green-500 rounded-full mr-2"></span>
                  <span className="font-medium">Connected</span>
                </div>
                <div className="text-sm text-gray-700 space-y-1">
                  <div><strong>Name:</strong> {connection.display_name || 'N/A'}</div>
                  <div><strong>Account:</strong> {connection.account_id}</div>
                  <div><strong>Cloud:</strong> {connection.cloud_id}</div>
                </div>
                <button
                  onClick={logout}
                  disabled={loading}
                  className="mt-3 text-sm text-red-600 hover:text-red-800 disabled:opacity-50"
                >
                  Disconnect
                </button>
              </div>
            ) : (
              <div className="text-red-600">
                <div className="flex items-center justify-center mb-2">
                  <span className="w-3 h-3 bg-red-500 rounded-full mr-2"></span>
                  <span className="font-medium">Not Connected</span>
                </div>
                <div className="text-sm text-gray-600 mb-3">
                  {connection.message || 'Connect to Jira to use AI features'}
                </div>
                <button
                  onClick={startJiraAuth}
                  disabled={loading}
                  className="bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 rounded disabled:opacity-50"
                >
                  Connect to Jira
                </button>
              </div>
            )}
          </div>
        </div>
        
        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <button
            onClick={() => callAPI('/healthz')}
            disabled={loading}
            className="bg-green-500 hover:bg-green-600 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 shadow-md"
          >
            ✅ Health Check
          </button>
          
          <button
            onClick={() => callAPI('/metrics')}
            disabled={loading}
            className="bg-purple-500 hover:bg-purple-600 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 shadow-md"
          >
            📊 System Metrics
          </button>
          
          <button
            onClick={() => callAPI('/auth/connection')}
            disabled={loading}
            className="bg-indigo-500 hover:bg-indigo-600 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 shadow-md"
          >
            🔍 Connection Info
          </button>
          
          <button
            onClick={() => callAPI('/insights/sprint?boardId=DEMO')}
            disabled={loading}
            className="bg-teal-500 hover:bg-teal-600 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 shadow-md"
          >
            📈 Sprint Insights
          </button>
        </div>

        {/* Jira Data Helpers */}
        {connection.authenticated && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 className="text-2xl font-bold mb-4 text-center">📋 Jira Data Helpers</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                onClick={() => callAPI('/auth/jira/boards')}
                disabled={loading}
                className="bg-blue-500 hover:bg-blue-600 text-white font-semibold py-4 px-6 rounded-lg disabled:opacity-50 shadow-md"
              >
                📋 Get Jira Boards
                <div className="text-xs mt-1 opacity-75">List all accessible boards</div>
              </button>
              
              <button
                onClick={() => callAPI('/auth/jira/projects')}
                disabled={loading}
                className="bg-cyan-500 hover:bg-cyan-600 text-white font-semibold py-4 px-6 rounded-lg disabled:opacity-50 shadow-md"
              >
                🏗️ Get Jira Projects
                <div className="text-xs mt-1 opacity-75">List all accessible projects</div>
              </button>
            </div>
          </div>
        )}

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
              <div className="text-xs mt-1 opacity-75">Recent Jira activity</div>
            </button>
            
            <button
              onClick={() => callAuthenticatedAPI('/summarize/blockers')}
              disabled={loading}
              className="bg-red-500 hover:bg-red-600 text-white font-semibold py-4 px-6 rounded-lg disabled:opacity-50 shadow-md"
            >
              🚫 AI Blocker Analysis
              <div className="text-xs mt-1 opacity-75">Identify impediments</div>
            </button>
            
            <button
              onClick={() => callAPI('/summarize/retrospective?boardId=DEMO&sprintId=123')}
              disabled={loading}
              className="bg-emerald-500 hover:bg-emerald-600 text-white font-semibold py-4 px-6 rounded-lg disabled:opacity-50 shadow-md"
            >
              🔄 AI Retrospective
              <div className="text-xs mt-1 opacity-75">Sprint insights</div>
            </button>
          </div>
          
          {!connection.authenticated && (
            <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-yellow-800 text-sm">
                💡 <strong>Note:</strong> AI Standup Summary and Blocker Analysis require Jira connection for personalized insights. Retrospective works in demo mode.
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
            <h3 className="text-xl font-bold mb-3">🔐 Secure Authentication</h3>
            <p className="text-gray-600">
              OAuth 2.0 PKCE flow with persistent sessions and automatic token refresh
            </p>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-bold mb-3">📊 Real-time Data</h3>
            <p className="text-gray-600">
              Live Jira integration with your actual projects, sprints, and issues
            </p>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-bold mb-3">🤖 AI Intelligence</h3>
            <p className="text-gray-600">
              GPT-4 powered summaries, blocker detection, and retrospective insights
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