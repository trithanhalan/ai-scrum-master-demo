'use client'

import { useState, useEffect } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
// Get the board ID from your Jira instance
const BOARD_ID = '1' // TODO: Make this configurable

interface AuthStatus {
  authenticated: boolean
  cloud_id?: string
  account_id?: string
  expires_at?: string
  message?: string
  site_name?: string  // Add site name for display
}

// Keys used for localStorage
const STORAGE_KEYS = {
  CLOUD_ID: 'jira_cloud_id',
  ACCOUNT_ID: 'jira_account_id',
  BOARD_ID: 'jira_board_id',
  SITE_NAME: 'jira_site_name',
  AUTH_STATUS: 'jira_auth_status'
}

export default function Home() {
  const [result, setResult] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [authStatus, setAuthStatus] = useState<AuthStatus>({ authenticated: false })
  const [cloudId, setCloudId] = useState<string>('')
  const [boardId, setBoardId] = useState<string>(BOARD_ID)

  useEffect(() => {
    // Load stored auth state
    const loadStoredAuthState = async () => {
      // Try to load stored auth status first
      const storedAuthStatus = localStorage.getItem(STORAGE_KEYS.AUTH_STATUS)
      if (storedAuthStatus) {
        const parsedStatus = JSON.parse(storedAuthStatus)
        setAuthStatus(parsedStatus)
      }

      // Load cloud ID and verify auth
      const storedCloudId = localStorage.getItem(STORAGE_KEYS.CLOUD_ID)
      if (storedCloudId) {
        setCloudId(storedCloudId)
        const status = await checkAuthStatus(storedCloudId)
        if (!status.authenticated) {
          // If auth check fails, clear all stored auth data
          clearAuthData()
        }
      }
    }
    
    // Load board ID
    const storedBoardId = localStorage.getItem(STORAGE_KEYS.BOARD_ID)
    if (storedBoardId) {
      setBoardId(storedBoardId)
    }

    // Check for OAuth callback
    const urlParams = new URLSearchParams(window.location.search)
    const authResult = urlParams.get('auth')
    const cloudIdParam = urlParams.get('cloud_id')
    
    const handleOAuthCallback = async () => {
      if (authResult === 'success' && cloudIdParam) {
        // Set cloud ID immediately for visual feedback
        setCloudId(cloudIdParam)
        
        // Check auth status to get full user info
        const status = await checkAuthStatus(cloudIdParam)
        if (status.authenticated) {
          setResult(`🎉 Successfully connected to ${status.site_name || 'Jira'}!`)
        } else {
          setResult('❌ Connection failed: Could not verify authentication')
          clearAuthData()
        }
        
        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname)
      } else if (authResult === 'error') {
        const message = urlParams.get('message') || 'Authentication failed'
        setResult(`❌ Connection failed: ${message}`)
        clearAuthData()
        window.history.replaceState({}, document.title, window.location.pathname)
      } else {
        // If no OAuth callback, load stored auth state
        await loadStoredAuthState()
      }
    }

    handleOAuthCallback()
  }, [])

  const updateAuthStatus = (status: AuthStatus) => {
    setAuthStatus(status)
    
    if (status.authenticated) {
      // Store all auth data
      localStorage.setItem(STORAGE_KEYS.AUTH_STATUS, JSON.stringify(status))
      if (status.cloud_id) localStorage.setItem(STORAGE_KEYS.CLOUD_ID, status.cloud_id)
      if (status.account_id) localStorage.setItem(STORAGE_KEYS.ACCOUNT_ID, status.account_id)
      if (status.site_name) localStorage.setItem(STORAGE_KEYS.SITE_NAME, status.site_name)
    } else {
      // Clear auth data if not authenticated
      clearAuthData()
    }
  }

  const checkAuthStatus = async (id: string) => {
    try {
      const response = await fetch(`${API_URL}/auth/status?cloud_id=${id}`)
      const data = await response.json()
      updateAuthStatus(data)
      return data
    } catch (error) {
      console.error('Auth status check failed:', error)
      const status = { authenticated: false, message: 'Auth status check failed' }
      updateAuthStatus(status)
      return status
    }
  }

  const callAPI = async (endpoint: string) => {
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}${endpoint}`)
      const data = await response.json()
      
      if (!response.ok) {
        // Handle HTTP errors
        const errorMessage = data.detail || data.message || 'An error occurred'
        setResult(`❌ API Error: ${errorMessage}`)
        
        // Handle authentication errors
        if (response.status === 401 || response.status === 403) {
          setAuthStatus({ authenticated: false })
          localStorage.removeItem('cloudId')
          localStorage.removeItem('accountId')
        }
        return
      }
      
      setResult(JSON.stringify(data, null, 2))
    } catch (error) {
      console.error('API call failed:', error)
      setResult(`❌ Network Error: Please check your connection and try again`)
    } finally {
      setLoading(false)
    }
  }

  const startJiraAuth = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/auth/jira/login`)
      const data = await response.json()
      window.location.href = data.authorization_url
    } catch (error) {
      setResult(`OAuth Error: ${error}`)
      setLoading(false)
    }
  }

      const callAuthenticatedAPI = async (endpoint: string) => {
    if (!authStatus.authenticated) {
      setResult('❌ Please authenticate with Jira first')
      return
    }
    
    const storedCloudId = localStorage.getItem('cloudId')
    if (!storedCloudId) {
      setResult('❌ No cloud ID found. Please reconnect to Jira.')
      return
    }
    
    // Create URL with parameters
    const url = new URL(`${API_URL}${endpoint}`)
    url.searchParams.append('cloudId', storedCloudId)
    if (!url.searchParams.has('boardId')) {
      url.searchParams.append('boardId', boardId)
    }
    
    try {
      const response = await fetch(url.toString())
      const data = await response.json()
      
      if (!response.ok) {
        // Handle HTTP errors
        const errorMessage = data.detail || data.message || 'An error occurred'
        setResult(`❌ API Error: ${errorMessage}`)
        
        // Handle authentication errors
        if (response.status === 401 || response.status === 403) {
          setAuthStatus({ authenticated: false })
          localStorage.removeItem('cloudId')
          localStorage.removeItem('accountId')
        }
        return
      }
      
      setResult(JSON.stringify(data, null, 2))
    } catch (error) {
      console.error('API call failed:', error)
      setResult(`❌ Network Error: Please check your connection and try again`)
    } finally {
      setLoading(false)
    }
  }

      const handleSprintInsights = () => {
    if (!authStatus.authenticated) {
      setResult('❌ Please authenticate with Jira first')
      return
    }
    callAuthenticatedAPI('/insights/sprint')
  }

  const clearAuthData = () => {
    // Clear all auth-related data from localStorage
    localStorage.removeItem(STORAGE_KEYS.CLOUD_ID)
    localStorage.removeItem(STORAGE_KEYS.ACCOUNT_ID)
    localStorage.removeItem(STORAGE_KEYS.SITE_NAME)
    localStorage.removeItem(STORAGE_KEYS.AUTH_STATUS)
    
    // Reset state
    setCloudId('')
    setAuthStatus({ authenticated: false })
  }

  const handleLogout = async () => {
    setLoading(true)
    try {
      // Call logout endpoint if we have a cloud ID
      if (cloudId) {
        await fetch(`${API_URL}/auth/logout`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ cloud_id: cloudId })
        })
      }
    } catch (error) {
      console.error('Logout failed:', error)
    } finally {
      // Clear auth data regardless of logout API success
      clearAuthData()
      setResult('')
      setLoading(false)
    }
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
              <div>
                <div className="text-green-600">
                  ✅ Connected to Jira
                  <div className="text-sm text-gray-600 mt-1 flex items-center justify-center gap-2">
                    Account: {authStatus.account_id}
                    <button
                      onClick={async () => {
                        const storedCloudId = localStorage.getItem('cloudId')
                        if (!storedCloudId) return
                        
                        try {
                          const response = await fetch(`${API_URL}/auth/me?cloud_id=${storedCloudId}`)
                          const data = await response.json()
                          setResult(JSON.stringify(data, null, 2))
                        } catch (error) {
                          setResult(`Error getting user info: ${error}`)
                        }
                      }}
                      className="text-blue-500 hover:text-blue-600"
                    >
                      ℹ️
                    </button>
                  </div>
                  <div className="text-sm text-gray-600 flex items-center justify-center gap-2">
                    Board ID: 
                    <input 
                      type="text" 
                      value={boardId}
                      onChange={(e) => {
                        setBoardId(e.target.value)
                        localStorage.setItem('boardId', e.target.value)
                      }}
                      className="border rounded px-2 py-1 w-20 text-center"
                    />
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="mt-2 text-sm text-red-600 hover:text-red-700"
                >
                  Disconnect
                </button>
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
            onClick={handleSprintInsights}
            disabled={loading || !authStatus.authenticated}
            className="bg-indigo-500 hover:bg-indigo-600 text-white font-semibold py-3 px-6 rounded-lg disabled:opacity-50 shadow-md"
          >
            📈 Sprint Insights
          </button>
          
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
              disabled={loading || !authStatus.authenticated}
              className="bg-orange-500 hover:bg-orange-600 text-white font-semibold py-4 px-6 rounded-lg disabled:opacity-50 shadow-md"
            >
              📋 AI Standup Summary
            </button>
            
            <button
              onClick={() => callAuthenticatedAPI('/summarize/blockers')}
              disabled={loading || !authStatus.authenticated}
              className="bg-red-500 hover:bg-red-600 text-white font-semibold py-4 px-6 rounded-lg disabled:opacity-50 shadow-md"
            >
              🚫 AI Blocker Analysis
            </button>
            
            <button
              onClick={() => callAuthenticatedAPI('/summarize/retrospective')}
              disabled={loading || !authStatus.authenticated}
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