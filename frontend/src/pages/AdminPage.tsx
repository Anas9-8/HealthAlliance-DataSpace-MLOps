import { useEffect, useState } from 'react'
import { Trash2, Plus, RefreshCw, Play, Users, Brain } from 'lucide-react'
import { getUsers, createUser, deleteUser, triggerRetrain, getRetrainStatus } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import type { User, TrainingStatus } from '../types'

export default function AdminPage() {
  const { user: me } = useAuth()
  const [users, setUsers] = useState<User[]>([])
  const [usersLoading, setUsersLoading] = useState(true)
  const [newUsername, setNewUsername] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [newRole, setNewRole] = useState('user')
  const [createError, setCreateError] = useState('')
  const [createSuccess, setCreateSuccess] = useState('')

  const [nPatients, setNPatients] = useState(1000)
  const [trainStatus, setTrainStatus] = useState<TrainingStatus | null>(null)
  const [trainError, setTrainError] = useState('')
  const [polling, setPolling] = useState(false)

  const loadUsers = () => {
    setUsersLoading(true)
    getUsers().then(setUsers).catch(console.error).finally(() => setUsersLoading(false))
  }

  const loadTrainStatus = () => {
    getRetrainStatus().then(setTrainStatus).catch(console.error)
  }

  useEffect(() => { loadUsers(); loadTrainStatus() }, [])

  useEffect(() => {
    if (!polling) return
    const id = setInterval(() => {
      getRetrainStatus().then((s) => {
        setTrainStatus(s)
        if (!s.running) setPolling(false)
      })
    }, 2000)
    return () => clearInterval(id)
  }, [polling])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreateError('')
    setCreateSuccess('')
    try {
      await createUser(newUsername, newPassword, newRole)
      setCreateSuccess(`User "${newUsername}" created successfully.`)
      setNewUsername(''); setNewPassword(''); setNewRole('user')
      loadUsers()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setCreateError(msg ?? 'Failed to create user')
    }
  }

  const handleDelete = async (id: number, username: string) => {
    if (!confirm(`Delete user "${username}"?`)) return
    try { await deleteUser(id); loadUsers() }
    catch { alert('Failed to delete user') }
  }

  const handleRetrain = async () => {
    setTrainError('')
    try {
      await triggerRetrain(nPatients)
      setPolling(true)
      loadTrainStatus()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setTrainError(msg ?? 'Failed to start retraining')
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* User Management */}
      <div className="bg-white rounded-xl border shadow-sm p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold text-gray-800 flex items-center gap-2">
            <Users size={18} className="text-blue-600" /> User Management
          </h2>
          <button onClick={loadUsers} className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1">
            <RefreshCw size={14} /> Refresh
          </button>
        </div>

        {/* Users table */}
        <div className="overflow-x-auto mb-6">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b">
                <th className="pb-2 font-medium text-gray-500">ID</th>
                <th className="pb-2 font-medium text-gray-500">Username</th>
                <th className="pb-2 font-medium text-gray-500">Role</th>
                <th className="pb-2 font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody>
              {usersLoading ? (
                <tr><td colSpan={4} className="py-4 text-center text-gray-400">Loading…</td></tr>
              ) : users.map((u) => (
                <tr key={u.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="py-2.5 font-mono text-gray-500">{u.id}</td>
                  <td className="py-2.5 font-medium text-gray-800">{u.username} {u.username === me?.username && <span className="text-xs text-gray-400">(you)</span>}</td>
                  <td className="py-2.5">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${u.role === 'admin' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'}`}>
                      {u.role}
                    </span>
                  </td>
                  <td className="py-2.5">
                    {u.username !== me?.username && (
                      <button onClick={() => handleDelete(u.id, u.username)} className="text-red-500 hover:text-red-700 p-1 rounded hover:bg-red-50">
                        <Trash2 size={14} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Create user */}
        <div className="border-t pt-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <Plus size={14} /> Create New User
          </h3>
          {createError && <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2 mb-3">{createError}</p>}
          {createSuccess && <p className="text-xs text-green-600 bg-green-50 border border-green-200 rounded px-3 py-2 mb-3">{createSuccess}</p>}
          <form onSubmit={handleCreate} className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <input type="text" placeholder="Username" value={newUsername} onChange={(e) => setNewUsername(e.target.value)} required
              className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            <input type="password" placeholder="Password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required
              className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            <select value={newRole} onChange={(e) => setNewRole(e.target.value)}
              className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
            <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg px-4 py-2 transition-colors">
              Create
            </button>
          </form>
        </div>
      </div>

      {/* Model Retraining */}
      <div className="bg-white rounded-xl border shadow-sm p-6">
        <h2 className="text-base font-semibold text-gray-800 flex items-center gap-2 mb-5">
          <Brain size={18} className="text-green-600" /> Model Retraining
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Training samples</label>
            <input type="number" min={100} max={10000} value={nPatients} onChange={(e) => setNPatients(Number(e.target.value))}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500" />
          </div>
          <div className="flex items-end">
            <button onClick={handleRetrain} disabled={trainStatus?.running}
              className="flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:opacity-60 text-white text-sm font-medium rounded-lg px-5 py-2 transition-colors">
              <Play size={14} />
              {trainStatus?.running ? 'Training…' : 'Start Retraining'}
            </button>
          </div>
        </div>

        {trainError && <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2 mb-3">{trainError}</p>}

        {trainStatus && (
          <div className="bg-gray-50 rounded-lg p-4 text-sm space-y-2">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${trainStatus.running ? 'bg-yellow-400 animate-pulse' : trainStatus.completed_at ? 'bg-green-500' : 'bg-gray-300'}`} />
              <span className="font-medium text-gray-700">
                {trainStatus.running ? 'Training in progress…' : trainStatus.completed_at ? 'Last training completed' : 'No training run yet'}
              </span>
            </div>
            {trainStatus.started_at && <p className="text-gray-500 text-xs">Started: {new Date(trainStatus.started_at).toLocaleString()}</p>}
            {trainStatus.completed_at && <p className="text-gray-500 text-xs">Completed: {new Date(trainStatus.completed_at).toLocaleString()}</p>}
            {trainStatus.current_roc_auc && (
              <p className="text-green-700 font-semibold">ROC-AUC: {trainStatus.current_roc_auc.toFixed(4)}</p>
            )}
            {trainStatus.error && <p className="text-red-600 text-xs">Error: {trainStatus.error}</p>}
          </div>
        )}
      </div>
    </div>
  )
}
