import { Routes, Route } from 'react-router-dom'

function Placeholder() {
  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-white mb-2">FairShare</h1>
        <p className="text-gray-500">Split expenses fairly with friends</p>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="*" element={<Placeholder />} />
    </Routes>
  )
}
