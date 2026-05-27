'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { api, getUserId } from '@/lib/api'

export default function Home() {
  const router = useRouter()
  const [startDate, setStartDate] = useState('2023-01-03')
  const [duration, setDuration] = useState('1month')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleStart = async () => {
    setLoading(true)
    setError('')
    try {
      const userName = getUserId()
      const data = await api('/game/start', {
        method: 'POST',
        body: JSON.stringify({ start_date: startDate, duration, user_name: userName }),
      })
      router.push(`/game/${data.game_id}`)
    } catch (e: any) {
      setError(e.message || '启动失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-lg mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-center mb-2">🎯 我不是股神</h1>
      <p className="text-center text-gray-500 mb-8">穿越回过去，用真实A股数据炒股，看看你能不能跑赢大盘！</p>

      <div className="bg-white rounded-xl shadow p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium mb-1">选择穿越日期</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            min="2010-01-01"
            max="2024-12-31"
            className="w-full border rounded-lg px-3 py-2"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">交易时间跨度</label>
          <div className="grid grid-cols-3 gap-2">
            {[
              { v: '1month', l: '1个月' },
              { v: '3month', l: '3个月' },
              { v: '1year', l: '1年' },
            ].map((opt) => (
              <button
                key={opt.v}
                onClick={() => setDuration(opt.v)}
                className={`py-2 rounded-lg border text-sm font-medium transition ${
                  duration === opt.v ? 'bg-blue-600 text-white border-blue-600' : 'bg-white hover:bg-gray-50'
                }`}
              >
                {opt.l}
              </button>
            ))}
          </div>
        </div>

        {error && <p className="text-red-500 text-sm">{error}</p>}

        <button
          onClick={handleStart}
          disabled={loading}
          className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? '正在穿越...' : '开始穿越 🚀'}
        </button>
      </div>

      <div className="mt-6 text-center">
        <a href="/rank" className="text-blue-600 text-sm hover:underline">查看排行榜 →</a>
      </div>

      <p className="mt-8 text-xs text-gray-400 text-center">
        ⚠️ 免责声明：本游戏使用历史数据，仅供娱乐，不构成任何投资建议。
      </p>
    </div>
  )
}
