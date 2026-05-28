'use client'
import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { api } from '@/lib/api'

interface Position {
  symbol: string
  name?: string
  amount: number
  cost_price: number
  buy_date: string
  current_price?: number
}

interface GameStatus {
  game_id: string
  current_date: string
  cash: number
  positions: Position[]
  total_assets: number
  game_over: boolean
  days_left?: number
  start_date?: string
  end_date?: string
}

interface StockInfo {
  symbol: string
  name: string
}

interface KlineData {
  open: number
  high: number
  low: number
  close: number
  volume: number
  change_pct?: number
}

export default function GamePage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [status, setStatus] = useState<GameStatus | null>(null)
  const [stocks, setStocks] = useState<StockInfo[]>([])
  const [keyword, setKeyword] = useState('')
  const [selectedStock, setSelectedStock] = useState<StockInfo | null>(null)
  const [kline, setKline] = useState<KlineData | null>(null)
  const [amount, setAmount] = useState('')
  const [action, setAction] = useState<'buy' | 'sell'>('buy')
  const [trades, setTrades] = useState<any[]>([])
  const [showTrades, setShowTrades] = useState(false)
  const [msg, setMsg] = useState('')
  const [loading, setLoading] = useState(false)
  const [autoPlay, setAutoPlay] = useState(true)
  const [speed, setSpeed] = useState(1) // 1=1x, 2=2x, 3=3x
  const autoPlayRef = useRef(true)
  const speedRef = useRef(1)

  useEffect(() => { autoPlayRef.current = autoPlay }, [autoPlay])
  useEffect(() => { speedRef.current = speed }, [speed])

  useEffect(() => {
    if (!autoPlay) return
    const getInterval = () => Math.round(3000 / speedRef.current)
    let timer: NodeJS.Timeout
    const tick = async () => {
      if (!autoPlayRef.current) return
      try {
        const data = await api(`/game/${id}/next-day`, { method: 'POST' })
        if (data.game_over) { setAutoPlay(false); router.push(`/result/${id}`); return }
        const st = await api(`/game/${id}/status`)
        setStatus(st)
      } catch { setAutoPlay(false) }
      if (autoPlayRef.current) timer = setTimeout(tick, getInterval())
    }
    timer = setTimeout(tick, getInterval())
    return () => clearTimeout(timer)
  }, [autoPlay, id, router])

  const fetchStatus = useCallback(async () => {
    try {
      const data = await api(`/game/${id}/status`)
      setStatus(data)
      if (data.game_over) {
        router.push(`/result/${id}`)
      }
    } catch {}
  }, [id, router])

  useEffect(() => { fetchStatus() }, [fetchStatus])

  const searchStocks = async (kw: string) => {
    setKeyword(kw)
    if (kw.length < 1) { setStocks([]); return }
    try {
      const data = await api(`/market/stocks?keyword=${encodeURIComponent(kw)}`)
      setStocks(data.stocks || [])
    } catch {}
  }

  const selectStock = async (stock: StockInfo) => {
    setSelectedStock(stock)
    setStocks([])
    setKeyword(stock.name)
    if (status) {
      try {
        const data = await api(`/market/kline/${stock.symbol}?date=${status.current_date}`)
        setKline(data)
      } catch { setKline(null) }
    }
  }

  const handleTrade = async () => {
    if (!selectedStock || !amount) return
    const amt = parseInt(amount)
    if (isNaN(amt) || amt <= 0 || amt % 100 !== 0) {
      setMsg('股数必须是100的正整数倍')
      return
    }
    setLoading(true)
    setMsg('')
    try {
      const data = await api(`/game/${id}/trade`, {
        method: 'POST',
        body: JSON.stringify({ symbol: selectedStock.symbol, action, amount: amt }),
      })
      setMsg(data.message || (data.success ? '交易成功' : '交易失败'))
      fetchStatus()
    } catch (e: any) {
      setMsg(e.message || '交易失败')
    } finally {
      setLoading(false)
    }
  }

  const handleNextDay = async () => {
    setLoading(true)
    try {
      const data = await api(`/game/${id}/next-day`, { method: 'POST' })
      if (data.game_over) { router.push(`/result/${id}`); return }
      fetchStatus()
      if (selectedStock && data.current_date) {
        try {
          const k = await api(`/market/kline/${selectedStock.symbol}?date=${data.current_date}`)
          setKline(k)
        } catch {}
      }
    } catch (e: any) { setMsg(e.message) }
    finally { setLoading(false) }
  }

  const handleFastForward = async () => {
    if (!confirm('确定快进到结束？持仓将按最后一天收盘价清算。')) return
    setLoading(true)
    try {
      await api(`/game/${id}/fast-forward`, { method: 'POST' })
      router.push(`/result/${id}`)
    } catch (e: any) { setMsg(e.message) }
    finally { setLoading(false) }
  }

  const loadTrades = async () => {
    try {
      const data = await api(`/game/${id}/trades`)
      setTrades(data.trades || [])
      setShowTrades(!showTrades)
    } catch {}
  }

  const setQuickAmount = (ratio: number) => {
    if (!status || !kline) return
    if (action === 'buy') {
      const maxShares = Math.floor((status.cash * ratio) / kline.close / 100) * 100
      setAmount(String(Math.max(maxShares, 0)))
    } else if (selectedStock) {
      const pos = status.positions.find(p => p.symbol === selectedStock.symbol)
      if (pos) setAmount(String(Math.floor(pos.amount * ratio / 100) * 100))
    }
  }

  if (!status) return <div className="flex justify-center items-center h-screen">加载中...</div>

  return (
    <div className="max-w-lg mx-auto px-4 py-4 space-y-4">
      {/* Header */}
      <div className="bg-white rounded-xl shadow p-4">
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>📅 <span className="font-medium">{status.current_date}</span></div>
          <div className="text-right">💰 现金: ¥{status.cash.toFixed(2)}</div>
          <div>📊 总资产: <span className="font-bold">¥{status.total_assets.toFixed(2)}</span></div>
          <div className="text-right text-gray-500">
            收益: <span className={status.total_assets >= 100000 ? 'text-red-500' : 'text-green-600'}>
              {((status.total_assets - 100000) / 1000).toFixed(2)}%
            </span>
          </div>
        </div>
      </div>

      {/* Stock Search */}
      <div className="bg-white rounded-xl shadow p-4 space-y-3">
        <div className="relative">
          <input
            type="text"
            placeholder="搜索股票代码或名称..."
            value={keyword}
            onChange={(e) => searchStocks(e.target.value)}
            className="w-full border rounded-lg px-3 py-2 text-sm"
          />
          {stocks.length > 0 && (
            <div className="absolute z-10 w-full bg-white border rounded-lg mt-1 max-h-40 overflow-y-auto shadow-lg">
              {stocks.map((s) => (
                <div key={s.symbol} onClick={() => selectStock(s)}
                  className="px-3 py-2 hover:bg-blue-50 cursor-pointer text-sm">
                  {s.symbol} - {s.name}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Kline info */}
        {kline && selectedStock && (
          <div className="border rounded-lg p-3 bg-gray-50">
            <div className="font-medium text-sm mb-2">{selectedStock.name} ({selectedStock.symbol})</div>
            <div className="grid grid-cols-4 gap-2 text-xs">
              <div>开: <span className="font-mono">{kline.open}</span></div>
              <div>高: <span className="text-red-500 font-mono">{kline.high}</span></div>
              <div>低: <span className="text-green-600 font-mono">{kline.low}</span></div>
              <div>收: <span className={`font-mono ${kline.close >= kline.open ? 'text-red-500' : 'text-green-600'}`}>{kline.close}</span></div>
            </div>
            <div className="text-xs text-gray-500 mt-1">成交量: {(kline.volume / 10000).toFixed(0)}万</div>
          </div>
        )}

        {/* Trade form */}
        {selectedStock && kline && (
          <div className="space-y-2">
            <div className="flex gap-2">
              <button onClick={() => setAction('buy')}
                className={`flex-1 py-1.5 rounded text-sm font-medium ${action === 'buy' ? 'bg-red-500 text-white' : 'border'}`}>
                买入
              </button>
              <button onClick={() => setAction('sell')}
                className={`flex-1 py-1.5 rounded text-sm font-medium ${action === 'sell' ? 'bg-green-600 text-white' : 'border'}`}>
                卖出
              </button>
            </div>
            <div className="flex gap-2 items-center">
              <input type="number" placeholder="股数(100的倍数)" value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="flex-1 border rounded px-3 py-2 text-sm" step="100" min="100" />
            </div>
            <div className="flex gap-1">
              {[{ r: 0.25, l: '1/4仓' }, { r: 0.5, l: '半仓' }, { r: 1, l: '全仓' }].map(q => (
                <button key={q.l} onClick={() => setQuickAmount(q.r)}
                  className="flex-1 text-xs py-1 border rounded hover:bg-gray-50">{q.l}</button>
              ))}
            </div>
            <button onClick={handleTrade} disabled={loading}
              className={`w-full py-2 rounded font-medium text-white ${action === 'buy' ? 'bg-red-500 hover:bg-red-600' : 'bg-green-600 hover:bg-green-700'} disabled:opacity-50`}>
              {loading ? '处理中...' : action === 'buy' ? '确认买入' : '确认卖出'}
            </button>
          </div>
        )}
        {msg && <p className="text-sm text-center text-blue-600">{msg}</p>}
      </div>

      {/* Positions */}
      {status.positions.length > 0 && (
        <div className="bg-white rounded-xl shadow p-4">
          <h3 className="font-medium text-sm mb-2">📦 持仓</h3>
          <div className="space-y-2">
            {status.positions.map((p) => (
              <div key={p.symbol} className="flex justify-between items-center text-sm border-b pb-2">
                <div>
                  <div className="font-medium">{p.name || p.symbol}</div>
                  <div className="text-xs text-gray-500">{p.amount}股 · 成本 ¥{p.cost_price.toFixed(2)}</div>
                </div>
                <div className="text-right">
                  {p.current_price && (
                    <div className={p.current_price >= p.cost_price ? 'text-red-500' : 'text-green-600'}>
                      ¥{p.current_price.toFixed(2)}
                      <span className="text-xs ml-1">
                        {((p.current_price - p.cost_price) / p.cost_price * 100).toFixed(1)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Trades */}
      <div className="bg-white rounded-xl shadow p-4">
        <button onClick={loadTrades} className="text-sm text-blue-600 hover:underline">
          {showTrades ? '收起交易记录' : '查看交易记录'} 📋
        </button>
        {showTrades && trades.length > 0 && (
          <div className="mt-2 space-y-1 max-h-40 overflow-y-auto">
            {trades.map((t, i) => (
              <div key={i} className="text-xs flex justify-between border-b py-1">
                <span>{t.date} {t.action === 'buy' ? '买入' : '卖出'} {t.symbol}</span>
                <span>{t.amount}股 @ ¥{t.price}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button onClick={() => setAutoPlay(!autoPlay)}
          className={`flex-1 py-3 rounded-xl font-medium ${autoPlay ? 'bg-yellow-500 text-white hover:bg-yellow-600' : 'bg-purple-600 text-white hover:bg-purple-700'}`}>
          {autoPlay ? '⏸ 暂停' : '▶ 播放'}
        </button>
        <button onClick={() => setSpeed(speed >= 3 ? 1 : speed + 1)}
          className="py-3 px-5 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700">
          x{speed}
        </button>
        <button onClick={handleFastForward} disabled={loading}
          className="py-3 px-4 bg-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-300 disabled:opacity-50">
          ⏭ 跳到结束
        </button>
      </div>
    </div>
  )
}
