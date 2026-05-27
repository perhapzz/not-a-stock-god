'use client'
import { useState, useEffect } from 'react'
import { api } from '@/lib/api'

interface RankItem {
  user_name: string
  start_date: string
  duration: string
  profit_rate: number
  final_assets: number
}

export default function RankPage() {
  const [ranks, setRanks] = useState<RankItem[]>([])

  useEffect(() => {
    api('/rank').then(d => setRanks(d.ranks || [])).catch(() => {})
  }, [])

  const durationLabel = (d: string) => ({ '1month': '1个月', '3month': '3个月', '1year': '1年' }[d] || d)

  return (
    <div className="max-w-lg mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-center mb-6">🏆 排行榜</h1>

      {ranks.length === 0 ? (
        <p className="text-center text-gray-500">暂无数据，快去玩一局吧！</p>
      ) : (
        <div className="bg-white rounded-xl shadow overflow-hidden">
          {ranks.map((r, i) => (
            <div key={i} className="flex items-center px-4 py-3 border-b last:border-0">
              <div className="w-8 text-center font-bold text-lg">
                {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i + 1}`}
              </div>
              <div className="flex-1 ml-3">
                <div className="font-medium text-sm">{r.user_name || '匿名玩家'}</div>
                <div className="text-xs text-gray-500">{r.start_date} · {durationLabel(r.duration)}</div>
              </div>
              <div className={`font-bold ${r.profit_rate >= 0 ? 'text-red-500' : 'text-green-600'}`}>
                {r.profit_rate >= 0 ? '+' : ''}{r.profit_rate}%
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-6 text-center">
        <a href="/" className="text-blue-600 text-sm hover:underline">← 返回首页</a>
      </div>
    </div>
  )
}
