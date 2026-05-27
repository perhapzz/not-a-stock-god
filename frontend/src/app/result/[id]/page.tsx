'use client'
import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { api } from '@/lib/api'

export default function ResultPage() {
  const { id } = useParams<{ id: string }>()
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const data = await api(`/game/${id}/settle`, { method: 'POST' })
        setResult(data)
      } catch (e: any) {
        // maybe already settled, try status
        try {
          const data = await api(`/game/${id}/status`)
          setResult(data)
        } catch (e2: any) {
          setError(e.message)
        }
      }
    }
    load()
  }, [id])

  if (error) return <div className="max-w-lg mx-auto px-4 py-8 text-center text-red-500">{error}</div>
  if (!result) return <div className="flex justify-center items-center h-screen">结算中...</div>

  const profitRate = result.profit_rate ?? ((result.total_assets - 100000) / 1000)
  const totalAssets = result.total_assets ?? result.final_assets ?? 100000

  return (
    <div className="max-w-lg mx-auto px-4 py-8 space-y-6">
      <h1 className="text-2xl font-bold text-center">🏁 游戏结束</h1>

      <div className="bg-white rounded-xl shadow p-6 space-y-4">
        <div className="text-center">
          <div className="text-sm text-gray-500">最终资产</div>
          <div className="text-3xl font-bold">¥{totalAssets.toFixed(2)}</div>
        </div>

        <div className="text-center">
          <div className="text-sm text-gray-500">收益率</div>
          <div className={`text-2xl font-bold ${profitRate >= 0 ? 'text-red-500' : 'text-green-600'}`}>
            {profitRate >= 0 ? '+' : ''}{profitRate.toFixed(2)}%
          </div>
        </div>

        {result.benchmark_rate !== undefined && (
          <div className="text-center border-t pt-3">
            <div className="text-sm text-gray-500">大盘同期涨幅</div>
            <div className={`text-lg font-medium ${result.benchmark_rate >= 0 ? 'text-red-500' : 'text-green-600'}`}>
              {result.benchmark_rate >= 0 ? '+' : ''}{result.benchmark_rate.toFixed(2)}%
            </div>
            <div className="text-sm mt-1">
              {profitRate > result.benchmark_rate ? '🎉 你跑赢了大盘！' : '😅 没能跑赢大盘'}
            </div>
          </div>
        )}

        {result.trade_count !== undefined && (
          <div className="border-t pt-3 grid grid-cols-2 gap-2 text-sm text-center">
            <div><span className="text-gray-500">交易次数</span><br/><span className="font-medium">{result.trade_count}</span></div>
            <div><span className="text-gray-500">持仓天数</span><br/><span className="font-medium">{result.duration || '-'}</span></div>
          </div>
        )}
      </div>

      <div className="flex gap-3">
        <a href="/" className="flex-1 py-3 bg-blue-600 text-white rounded-xl font-medium text-center hover:bg-blue-700">
          再来一局
        </a>
        <a href="/rank" className="flex-1 py-3 bg-gray-200 text-gray-700 rounded-xl font-medium text-center hover:bg-gray-300">
          排行榜
        </a>
      </div>
    </div>
  )
}
